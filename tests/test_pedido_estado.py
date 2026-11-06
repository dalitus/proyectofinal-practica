"""Tests del ciclo de vida del pedido (T-044, D-010).

Corren contra `zapateria_test`. Cada test crea el pedido por el camino real
(carrito + checkout), asi que el stock que se repone al cancelar es el que la
compra desconto de verdad, no un numero inventado por el test.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest
from reflex_local_auth.local_auth import LocalUser
from sqlmodel import Session, select

from app.model.categoria_modelo import Categoria
from app.model.pedido_modelo import Pedido
from app.model.producto_modelo import Producto
from app.model.variante_modelo import Stocks
from app.repository import pedido_repositorio
from app.repository.pedido_repositorio import EstadoCambiado
from app.service.carrito_servicio import agregar
from app.service.pedido_servicio import (
    ErrorDePedido,
    cambiar_estado,
    cancelar_pedido,
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


def _crear_comprador(session: Session, email: str = "ana@example.com") -> LocalUser:
    usuario = LocalUser(
        username=email,
        password_hash=LocalUser.hash_password("secreto123"),
        enabled=True,
    )
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario


def _crear_producto(
    session: Session,
    *,
    precio: str = "10000.00",
    variantes: list[tuple[str, str, int]] | None = None,
) -> tuple[Producto, list[Stocks]]:
    categoria = Categoria(nombre="Running")
    session.add(categoria)
    session.commit()
    session.refresh(categoria)

    producto = Producto(
        nombre="Zapatilla Running Air",
        marca="Fermin",
        precio=Decimal(precio),
        categoria_id=categoria.id,
        activo=True,
    )
    session.add(producto)
    session.commit()
    session.refresh(producto)

    stocks: list[Stocks] = []
    for color, talle, cantidad in variantes or [("Blanco", "40", 5)]:
        variante = Stocks(
            producto_id=producto.id,
            color=color,
            talle=talle,
            cantidad_disponible=cantidad,
        )
        session.add(variante)
        stocks.append(variante)
    session.commit()
    for variante in stocks:
        session.refresh(variante)

    return producto, stocks


def _comprar(
    session: Session,
    *,
    cantidades: list[int] | None = None,
    variantes: list[tuple[str, str, int]] | None = None,
) -> tuple[int, list[Stocks]]:
    """Buy through cart + checkout and return the order id with its variants."""
    comprador = _crear_comprador(session)
    usuario_id = comprador.id or 0
    _, stocks = _crear_producto(session, variantes=variantes)

    for variante, cantidad in zip(stocks, cantidades or [1] * len(stocks), strict=False):
        agregar(usuario_id, variante.id_stock or 0, cantidad)

    pedido_id = confirmar_pedido(usuario_id, validar_entrega(ENTREGA))
    session.rollback()  # cierra la transaccion de lectura del fixture
    return pedido_id, stocks


def _pedido(session: Session, pedido_id: int) -> Pedido:
    session.rollback()
    return session.exec(select(Pedido).where(Pedido.id_pedido == pedido_id)).one()


def _stock(session: Session, variantes: list[Stocks]) -> list[int]:
    session.rollback()
    for variante in variantes:
        session.refresh(variante)
    return [variante.cantidad_disponible for variante in variantes]


def test_en_espera_pasa_a_enviado(session: Session) -> None:
    pedido_id, _ = _comprar(session)

    assert cambiar_estado(pedido_id, "enviado") == "enviado"

    pedido = _pedido(session, pedido_id)
    assert pedido.estado == "enviado"
    assert pedido.fecha_entrega is None
    assert pedido.fecha_cancelacion is None


def test_enviado_pasa_a_entregado_y_registra_fecha(session: Session) -> None:
    pedido_id, _ = _comprar(session)
    cambiar_estado(pedido_id, "enviado")

    cambiar_estado(pedido_id, "entregado")

    pedido = _pedido(session, pedido_id)
    assert pedido.estado == "entregado"
    assert pedido.fecha_entrega is not None
    # MySQL guarda DATETIME sin fracciones: se compara contra el reloj con holgura.
    assert abs((datetime.now() - pedido.fecha_entrega).total_seconds()) < 60
    assert pedido.fecha_cancelacion is None


@pytest.mark.parametrize("previo", ["en espera", "enviado"])
def test_cancelar_repone_stock_y_registra_fecha(session: Session, previo: str) -> None:
    pedido_id, stocks = _comprar(
        session,
        variantes=[("Blanco", "40", 5), ("Negro", "41", 4)],
        cantidades=[2, 1],
    )
    assert _stock(session, stocks) == [3, 3]

    if previo != "en espera":
        cambiar_estado(pedido_id, previo)

    assert cancelar_pedido(pedido_id) == "cancelado"

    pedido = _pedido(session, pedido_id)
    assert pedido.estado == "cancelado"
    assert pedido.fecha_cancelacion is not None
    assert abs((datetime.now() - pedido.fecha_cancelacion).total_seconds()) < 60
    assert pedido.fecha_entrega is None
    # Cada variante vuelve a la cantidad que tenia antes de la compra.
    assert _stock(session, stocks) == [5, 4]


def test_cancelar_dos_veces_no_repone_dos_veces(session: Session) -> None:
    pedido_id, stocks = _comprar(session, variantes=[("Blanco", "40", 5)], cantidades=[2])
    cancelar_pedido(pedido_id)

    with pytest.raises(ErrorDePedido) as error:
        cancelar_pedido(pedido_id)

    assert "cancelado" in str(error.value)
    assert _stock(session, stocks) == [5]


def test_entregado_no_se_puede_cancelar(session: Session) -> None:
    pedido_id, stocks = _comprar(session, variantes=[("Blanco", "40", 5)], cantidades=[2])
    cambiar_estado(pedido_id, "enviado")
    cambiar_estado(pedido_id, "entregado")

    with pytest.raises(ErrorDePedido) as error:
        cancelar_pedido(pedido_id)

    assert "entregado" in str(error.value)
    assert "no se puede cambiar" in str(error.value)
    pedido = _pedido(session, pedido_id)
    assert pedido.fecha_cancelacion is None
    assert _stock(session, stocks) == [3]  # el stock sigue descontado


def test_en_espera_no_puede_saltar_a_entregado(session: Session) -> None:
    pedido_id, _ = _comprar(session)

    with pytest.raises(ErrorDePedido) as error:
        cambiar_estado(pedido_id, "entregado")

    assert "No se puede pasar de 'en espera' a 'entregado'" in str(error.value)
    assert _pedido(session, pedido_id).estado == "en espera"


def test_estado_desconocido_falla(session: Session) -> None:
    pedido_id, _ = _comprar(session)

    with pytest.raises(ErrorDePedido) as error:
        cambiar_estado(pedido_id, "perdido")

    assert "no existe" in str(error.value)
    assert _pedido(session, pedido_id).estado == "en espera"


def test_pedido_inexistente_falla(session: Session) -> None:
    with pytest.raises(ErrorDePedido) as error:
        cambiar_estado(9999, "enviado")

    assert "No existe el pedido #9999" in str(error.value)


def test_cancelar_repone_solo_las_variantes_del_pedido(session: Session) -> None:
    comprador = _crear_comprador(session)
    usuario_id = comprador.id or 0
    _, stocks = _crear_producto(
        session,
        variantes=[("Blanco", "40", 5), ("Negro", "41", 5)],
    )

    agregar(usuario_id, stocks[0].id_stock or 0, 2)
    pedido_cancelado = confirmar_pedido(usuario_id, validar_entrega(ENTREGA))
    agregar(usuario_id, stocks[0].id_stock or 0, 1)
    agregar(usuario_id, stocks[1].id_stock or 0, 2)
    pedido_activo = confirmar_pedido(usuario_id, validar_entrega(ENTREGA))

    session.rollback()
    assert _stock(session, stocks) == [2, 3]

    cancelar_pedido(pedido_cancelado)

    # Blanco recupera las 2 del pedido cancelado; Negro no se toca.
    assert _stock(session, stocks) == [4, 3]
    assert _pedido(session, pedido_activo).estado == "en espera"


def test_el_repositorio_rechaza_un_estado_esperado_que_ya_cambio(
    session: Session,
) -> None:
    pedido_id, _ = _comprar(session)

    with pytest.raises(EstadoCambiado) as error:
        pedido_repositorio.cambiar_estado(
            pedido_id=pedido_id,
            estado_esperado="enviado",
            estado_nuevo="entregado",
        )

    assert error.value.estado_actual == "en espera"
    assert error.value.estado_esperado == "enviado"
    assert _pedido(session, pedido_id).estado == "en espera"
