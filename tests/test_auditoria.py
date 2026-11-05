"""Tests del log de operaciones sensibles (T-053, D-031).

El log es la única auditoría: no hay tabla ni pantalla. Se verifica que haya una
línea por operación confirmada, con quién, qué y sobre qué, y que una operación
rechazada no deje rastro.
"""

from __future__ import annotations

import json
import logging
from decimal import Decimal

import pytest
from reflex_local_auth.local_auth import LocalUser
from sqlmodel import Session

from app.model.categoria_modelo import Categoria
from app.model.consulta_model import Consulta
from app.model.product_model import Producto
from app.model.stock_model import Stocks
from app.service.carrito_servicio import agregar
from app.service.auditoria import registrar
from app.service.configuracion_logs import configurar_logs
from app.service.consulta_servicio import eliminar as eliminar_consulta
from app.service.consulta_servicio import responder as responder_consulta
from app.service.pedido_servicio import (
    ErrorDePedido,
    cancelar_pedido,
    cambiar_estado,
    confirmar_pedido,
    validar_entrega,
)

ENTREGA = {
    "direccion": "San Martin",
    "numero": "1234",
    "departamento": "",
    "codigo_postal": "1425",
    "ciudad": "CABA",
    "provincia": "Buenos Aires",
}


def _lineas(caplog: pytest.LogCaptureFixture) -> list[dict]:
    return [
        json.loads(registro.message)
        for registro in caplog.records
        if registro.name == "app.auditoria"
    ]


def _comprador(session: Session, email: str = "ana@example.com") -> int:
    usuario = LocalUser(
        username=email,
        password_hash=LocalUser.hash_password("secreto123"),
        enabled=True,
    )
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario.id or 0


def _pedido(session: Session) -> int:
    usuario_id = _comprador(session)

    categoria = Categoria(nombre="Auditoria")
    session.add(categoria)
    session.commit()
    session.refresh(categoria)

    producto = Producto(
        nombre="Zapatilla Running Air",
        marca="Fermin",
        precio=Decimal("10000.00"),
        categoria_id=categoria.id,
        activo=True,
    )
    session.add(producto)
    session.commit()
    session.refresh(producto)

    variante = Stocks(
        producto_id=producto.id,
        color="Blanco",
        talle="40",
        cantidad_disponible=5,
    )
    session.add(variante)
    session.commit()
    session.refresh(variante)

    agregar(usuario_id, variante.id_stock or 0, 1)
    pedido_id = confirmar_pedido(usuario_id, validar_entrega(ENTREGA))
    session.rollback()
    return pedido_id


def _admin_id(session: Session) -> int:
    """An existing ``LocalUser``: ``respondido_por_id`` is a foreign key."""
    usuario = LocalUser(
        username="admin@example.com",
        password_hash=LocalUser.hash_password("admin1234"),
        enabled=True,
    )
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario.id or 0


def _consulta(session: Session) -> int:
    consulta = Consulta(
        usuario_id=_comprador(session, email="beto@example.com"),
        asunto="Consulta de talle",
        mensaje="Necesito saber si el 42 queda chico.",
    )
    session.add(consulta)
    session.commit()
    session.refresh(consulta)
    session.rollback()
    return consulta.id_consulta or 0


def test_el_destino_stdout_recibe_una_linea_por_operacion(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """D-035: la auditoría va a stdout, sin archivo (T-064)."""
    monkeypatch.setenv("REFLEX_ENV_MODE", "dev")
    logger = logging.getLogger("app")
    nivel_anterior = logger.level
    antes = list(logger.handlers)

    try:
        configurar_logs()
        # Idempotente: el arranque de Reflex importa la app más de una vez.
        configurar_logs()

        registrar(
            accion="cambiar_estado",
            entidad="pedido",
            entidad_id=9,
            admin_id=2,
            detalle="en espera -> enviado",
        )
        salida = capsys.readouterr().out
    finally:
        for handler in list(logger.handlers):
            if handler not in antes:
                logger.removeHandler(handler)
                handler.close()
        logger.setLevel(nivel_anterior)

    lineas = [
        linea for linea in salida.strip().splitlines() if "app.auditoria" in linea
    ]
    assert len(lineas) == 1
    assert json.loads(lineas[0].split("app.auditoria: ", 1)[1])["accion"] == (
        "cambiar_estado"
    )


def test_cambiar_estado_registra_admin_accion_y_entidad(
    session: Session,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="app.auditoria")
    pedido_id = _pedido(session)

    cambiar_estado(pedido_id, "enviado", admin_id=7)

    lineas = _lineas(caplog)
    assert len(lineas) == 1
    linea = lineas[0]
    assert linea["admin_id"] == 7
    assert linea["accion"] == "cambiar_estado"
    assert linea["entidad"] == "pedido"
    assert linea["entidad_id"] == pedido_id
    assert linea["detalle"] == "en espera -> enviado"
    assert linea["fecha"]


def test_cancelar_pedido_tiene_su_propia_accion(
    session: Session,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="app.auditoria")
    pedido_id = _pedido(session)

    cancelar_pedido(pedido_id, admin_id=3)

    linea = _lineas(caplog)[0]
    assert linea["accion"] == "cancelar_pedido"
    assert linea["detalle"] == "en espera -> cancelado"
    assert linea["admin_id"] == 3


def test_una_transicion_rechazada_no_se_audita(
    session: Session,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="app.auditoria")
    pedido_id = _pedido(session)

    with pytest.raises(ErrorDePedido):
        cambiar_estado(pedido_id, "entregado", admin_id=7)

    assert _lineas(caplog) == []


def test_responder_consulta_se_audita(
    session: Session,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="app.auditoria")
    consulta_id = _consulta(session)
    admin_id = _admin_id(session)

    responder_consulta(consulta_id, "Te queda bien el 42.", admin_id=admin_id)

    linea = _lineas(caplog)[0]
    assert linea["accion"] == "responder_consulta"
    assert linea["entidad"] == "consulta"
    assert linea["entidad_id"] == consulta_id
    assert linea["admin_id"] == admin_id


def test_eliminar_consulta_se_audita(
    session: Session,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="app.auditoria")
    consulta_id = _consulta(session)

    eliminar_consulta(consulta_id, admin_id=5)

    linea = _lineas(caplog)[0]
    assert linea["accion"] == "eliminar_consulta"
    assert linea["entidad_id"] == consulta_id
    assert linea["admin_id"] == 5


def test_sin_admin_id_igual_deja_la_linea(
    session: Session,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Mientras no exista la guarda de rol, se audita sin autor (T-023)."""
    caplog.set_level(logging.INFO, logger="app.auditoria")
    pedido_id = _pedido(session)

    cambiar_estado(pedido_id, "enviado")

    linea = _lineas(caplog)[0]
    assert linea["admin_id"] is None
    assert linea["accion"] == "cambiar_estado"
