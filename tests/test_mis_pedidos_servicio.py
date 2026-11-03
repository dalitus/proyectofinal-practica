"""Tests del historial de pedidos del comprador (T-076, D-002).

Se insertan pedidos directo: aca se prueba el alcance por dueno, la paginacion y
el detalle, no el checkout (que ya tiene sus tests en `test_pedido_servicio.py`).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from reflex_local_auth.local_auth import LocalUser
from sqlmodel import Session

from app.model.categoria_modelo import Categoria
from app.model.pedido_item_modelo import PedidoItem
from app.model.pedido_model import Pedido
from app.model.product_model import Producto
from app.model.stock_model import Stocks
from app.service.formato_moneda import formatear_precio
from app.service.pedido_servicio import (
    ErrorDePedido,
    listar_mis_pedidos,
    obtener_mi_pedido,
)

ENTREGA = {
    "direccion": "San Martin",
    "numero": "1234",
    "departamento": "4 B",
    "codigo_postal": "1425",
    "ciudad": "CABA",
    "provincia": "Buenos Aires",
}


def _comprador(session: Session, email: str = "ana@example.com") -> int:
    usuario = LocalUser(
        username=email,
        password_hash=LocalUser.hash_password("secreto123"),
        enabled=True,
    )
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    usuario_id = usuario.id or 0
    session.rollback()
    return usuario_id


def _variantes(session: Session, cantidad: int) -> list[int]:
    """Real ``stocks`` rows: ``pedido_items.variante_id`` has a foreign key."""
    categoria = Categoria(nombre="Running")
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

    ids: list[int] = []
    for indice in range(cantidad):
        variante = Stocks(
            producto_id=producto.id,
            color="Blanco" if indice % 2 == 0 else "Negro",
            talle=str(40 + indice),
            cantidad_disponible=5,
        )
        session.add(variante)
        session.commit()
        session.refresh(variante)
        ids.append(variante.id_stock or 0)
    session.rollback()
    return ids


def _pedido(
    session: Session,
    *,
    usuario_id: int,
    total: str = "10000.00",
    estado: str = "en espera",
    fecha: datetime | None = None,
    lineas: list[tuple[str, str, int, str]] | None = None,
) -> int:
    pedido = Pedido(
        usuario_id=usuario_id,
        estado=estado,
        total=Decimal(total),
        fecha_pedido=fecha or datetime.now(),
        **ENTREGA,
    )
    session.add(pedido)
    session.commit()
    session.refresh(pedido)
    pedido_id = pedido.id_pedido or 0

    if lineas:
        variantes = _variantes(session, len(lineas))
        for indice, (color, talle, cantidad, precio) in enumerate(lineas):
            session.add(
                PedidoItem(
                    pedido_id=pedido_id,
                    variante_id=variantes[indice],
                    color=color,
                    talle=talle,
                    cantidad=cantidad,
                    precio_unitario=Decimal(precio),
                )
            )
        session.commit()

    session.rollback()
    return pedido_id


def test_listado_solo_trae_los_pedidos_propios(session: Session) -> None:
    ana = _comprador(session)
    beto = _comprador(session, email="beto@example.com")
    _pedido(session, usuario_id=ana, total="10000.00")
    _pedido(session, usuario_id=beto, total="20000.00")

    pagina = listar_mis_pedidos(ana)

    assert pagina.total == 1
    assert [pedido.total for pedido in pagina.pedidos] == [formatear_precio("10000.00")]


def test_listado_ordena_lo_mas_nuevo_primero(session: Session) -> None:
    ana = _comprador(session)
    ahora = datetime.now()
    viejo = _pedido(session, usuario_id=ana, fecha=ahora - timedelta(days=2))
    nuevo = _pedido(session, usuario_id=ana, fecha=ahora)

    pagina = listar_mis_pedidos(ana)

    assert [pedido.id for pedido in pagina.pedidos] == [nuevo, viejo]


def test_listado_muestra_etiqueta_de_estado_y_total_formateado(session: Session) -> None:
    ana = _comprador(session)
    _pedido(session, usuario_id=ana, total="1234567.00", estado="enviado")

    pedido = listar_mis_pedidos(ana).pedidos[0]

    assert pedido.estado == "enviado"
    assert pedido.estado_etiqueta == "Enviado"
    assert pedido.total == "$ 1.234.567,00"


def test_listado_cuenta_unidades_de_las_lineas(session: Session) -> None:
    ana = _comprador(session)
    _pedido(
        session,
        usuario_id=ana,
        lineas=[("Blanco", "40", 2, "1000.00"), ("Negro", "41", 3, "1000.00")],
    )

    pedido = listar_mis_pedidos(ana).pedidos[0]

    assert pedido.unidades == 5


def test_listado_pagina_y_reencuadra_fuera_de_rango(session: Session) -> None:
    ana = _comprador(session)
    for indice in range(12):
        _pedido(session, usuario_id=ana, total=f"{indice + 1}000.00")

    primera = listar_mis_pedidos(ana)
    segunda = listar_mis_pedidos(ana, pagina=2)
    lejana = listar_mis_pedidos(ana, pagina=99)

    assert primera.total == 12
    assert primera.total_paginas == 2
    assert len(primera.pedidos) == 10
    assert primera.hay_siguiente is True
    assert len(segunda.pedidos) == 2
    assert segunda.pagina == 2
    assert lejana.pagina == 2


def test_detalle_trae_lineas_y_envio(session: Session) -> None:
    ana = _comprador(session)
    pedido_id = _pedido(
        session,
        usuario_id=ana,
        total="30000.00",
        lineas=[("Blanco", "40", 2, "10000.00"), ("Negro", "41", 1, "10000.00")],
    )

    detalle = obtener_mi_pedido(pedido_id, ana)

    assert detalle.id == pedido_id
    assert detalle.total == "$ 30.000,00"
    assert detalle.unidades == 3
    assert detalle.envio == "San Martin 1234, 4 B, CABA, Buenos Aires, CP 1425"
    assert [linea.cantidad for linea in detalle.lineas] == [2, 1]
    assert detalle.lineas[0].subtotal == "$ 20.000,00"


def test_detalle_de_otro_usuario_es_inexistente(session: Session) -> None:
    ana = _comprador(session)
    beto = _comprador(session, email="beto@example.com")
    pedido_id = _pedido(session, usuario_id=beto)

    with pytest.raises(ErrorDePedido) as error:
        obtener_mi_pedido(pedido_id, ana)

    assert "no existe" in str(error.value).lower()


def test_detalle_de_un_pedido_inexistente_falla(session: Session) -> None:
    ana = _comprador(session)

    with pytest.raises(ErrorDePedido):
        obtener_mi_pedido(999_999, ana)


def test_sin_sesion_falla(session: Session) -> None:
    with pytest.raises(ErrorDePedido):
        listar_mis_pedidos(0)

    with pytest.raises(ErrorDePedido):
        obtener_mi_pedido(1, 0)
