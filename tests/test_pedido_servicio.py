"""Tests del checkout y la creacion del pedido (T-043).

Corren contra `zapateria_test`: `conftest.py` apunta el engine del repositorio a
la base de test. Cada test arma su comprador, producto y variantes, y verifica la
transaccion completa: pedido, snapshot, stock descontado y carrito vaciado.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from reflex_local_auth.local_auth import LocalUser
from sqlmodel import Session, select

from app.model.categoria_modelo import Categoria
from app.model.consulta_modelo import Consulta
from app.model.pedido_item_modelo import PedidoItem
from app.model.pedido_modelo import Pedido
from app.model.perfil_modelo import UserProfile
from app.model.producto_modelo import Producto
from app.model.variante_modelo import Stocks
from app.service.carrito_servicio import agregar, ver_carrito
from app.service.pedido_servicio import (
    DatosDeEntrega,
    ErrorDePedido,
    confirmar_pedido,
    errores_de_entrega,
    validar_entrega,
)

ENTREGA = {
    "direccion": "San Martin",
    "numero": "1234",
    "departamento": "4 B",
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


def _crear_admin(session: Session, email: str = "admin@example.com") -> LocalUser:
    usuario = _crear_comprador(session, email)
    session.add(
        UserProfile(
            local_user_id=usuario.id,
            nombre="Admin",
            email=email,
            is_admin=True,
        )
    )
    session.commit()
    return usuario


def _crear_producto(
    session: Session,
    *,
    nombre: str = "Zapatilla Running Air",
    precio: str = "89999.00",
    activo: bool = True,
    variantes: list[tuple[str, str, int]] | None = None,
) -> tuple[Producto, list[Stocks]]:
    categoria = Categoria(nombre="Running")
    session.add(categoria)
    session.commit()
    session.refresh(categoria)

    producto = Producto(
        nombre=nombre,
        marca="Fermin",
        precio=Decimal(precio),
        categoria_id=categoria.id,
        activo=activo,
    )
    session.add(producto)
    session.commit()
    session.refresh(producto)

    stocks: list[Stocks] = []
    for color, talle, cantidad in variantes or [("Blanco", "40", 3)]:
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


def test_confirmar_crea_pedido_con_snapshot_y_vacia_el_carrito(session: Session) -> None:
    comprador = _crear_comprador(session)
    usuario_id = comprador.id or 0
    producto, stocks = _crear_producto(
        session,
        precio="10000.00",
        variantes=[("Blanco", "40", 5), ("Negro", "41", 5)],
    )
    agregar(usuario_id, stocks[0].id_stock or 0, 2)
    agregar(usuario_id, stocks[1].id_stock or 0, 1)

    pedido_id = confirmar_pedido(usuario_id, validar_entrega(ENTREGA))

    session.rollback()  # cierra la transaccion de lectura del fixture
    pedido = session.exec(select(Pedido).where(Pedido.id_pedido == pedido_id)).one()
    assert pedido.usuario_id == usuario_id
    assert pedido.estado == "en espera"
    assert pedido.total == Decimal("30000.00")
    assert pedido.direccion == "San Martin"
    assert pedido.numero == "1234"
    assert pedido.departamento == "4 B"
    assert pedido.codigo_postal == "1425"
    assert pedido.ciudad == "CABA"
    assert pedido.provincia == "Buenos Aires"

    items = session.exec(
        select(PedidoItem).where(PedidoItem.pedido_id == pedido_id).order_by(PedidoItem.color)
    ).all()
    assert len(items) == 2
    assert [item.color for item in items] == ["Blanco", "Negro"]
    assert [item.cantidad for item in items] == [2, 1]
    assert items[0].precio_unitario == Decimal("10000.00")
    assert items[0].talle == "40"

    # El stock se descuenta en la variante y el carrito queda vacio.
    assert ver_carrito(usuario_id).vacio is True
    for variante in stocks:
        session.refresh(variante)
    assert stocks[0].cantidad_disponible == 3
    assert stocks[1].cantidad_disponible == 4


def test_confirmar_con_carrito_vacio_falla_sin_crear_pedido(session: Session) -> None:
    comprador = _crear_comprador(session)
    usuario_id = comprador.id or 0

    with pytest.raises(ErrorDePedido) as error:
        confirmar_pedido(usuario_id, validar_entrega(ENTREGA))

    assert "carrito esta vacio" in str(error.value)
    assert session.exec(select(Pedido)).all() == []


def test_admin_no_puede_confirmar_pedido(session: Session) -> None:
    """D-050: the checkout rejects the admin even when the event is invoked directly."""
    admin = _crear_admin(session)
    admin_id = admin.id or 0

    with pytest.raises(ErrorDePedido) as error:
        confirmar_pedido(admin_id, validar_entrega(ENTREGA))

    assert str(error.value) == "El administrador no puede comprar."
    session.rollback()
    assert session.exec(select(Pedido)).all() == []


def test_stock_insuficiente_no_crea_pedido_ni_descuenta(session: Session) -> None:
    comprador = _crear_comprador(session)
    usuario_id = comprador.id or 0
    _, stocks = _crear_producto(session, variantes=[("Blanco", "40", 5)])
    variante = stocks[0]
    agregar(usuario_id, variante.id_stock or 0, 3)

    # Otra compra se llevo el stock despues de llenar el carrito (D-004).
    variante.cantidad_disponible = 1
    session.add(variante)
    session.commit()

    with pytest.raises(ErrorDePedido) as error:
        confirmar_pedido(usuario_id, validar_entrega(ENTREGA))

    assert "Quedan 1 unidades" in str(error.value)
    session.rollback()
    assert session.exec(select(Pedido)).all() == []
    assert session.exec(select(PedidoItem)).all() == []
    assert ver_carrito(usuario_id).total_unidades == 3
    assert session.exec(select(Stocks)).one().cantidad_disponible == 1


def test_producto_desactivado_entre_el_carrito_y_el_checkout(session: Session) -> None:
    comprador = _crear_comprador(session)
    usuario_id = comprador.id or 0
    producto, stocks = _crear_producto(session, variantes=[("Blanco", "40", 5)])
    agregar(usuario_id, stocks[0].id_stock or 0, 1)

    producto.activo = False
    session.add(producto)
    session.commit()

    with pytest.raises(ErrorDePedido):
        confirmar_pedido(usuario_id, validar_entrega(ENTREGA))

    session.rollback()
    assert session.exec(select(Pedido)).all() == []
    assert session.exec(select(Stocks)).one().cantidad_disponible == 5


def test_confirmar_no_crea_consulta_automatica(session: Session) -> None:
    """The order is the single source of truth (D-006, T-045).

    The checkout used to also write a ``Consulta`` with the subject
    ``Compra realizada``; it must not come back.
    """
    comprador = _crear_comprador(session)
    usuario_id = comprador.id or 0
    _, stocks = _crear_producto(session, variantes=[("Blanco", "40", 5)])
    agregar(usuario_id, stocks[0].id_stock or 0, 1)

    confirmar_pedido(usuario_id, validar_entrega(ENTREGA))

    session.rollback()
    assert session.exec(select(Consulta)).all() == []


def test_errores_de_entrega_por_campo() -> None:
    errores = errores_de_entrega({"direccion": "  ", "numero": "", "ciudad": "CABA"})

    assert errores == {
        "direccion": "Pone tu direccion.",
        "numero": "Pone el numero.",
        "provincia": "Pone tu provincia.",
    }


def test_validar_entrega_limpia_y_normaliza() -> None:
    datos = {
        "direccion": "  San Martin ",
        "numero": "1234 ",
        "departamento": "",
        "codigo_postal": " 1425 ",
        "ciudad": " CABA",
        "provincia": "Buenos Aires  ",
    }

    entrega = validar_entrega(datos)

    assert isinstance(entrega, DatosDeEntrega)
    assert entrega.direccion == "San Martin"
    assert entrega.numero == "1234"
    assert entrega.departamento == ""
    assert entrega.codigo_postal == "1425"
    assert entrega.ciudad == "CABA"
    assert entrega.provincia == "Buenos Aires"
    assert entrega.como_dict() == {
        "direccion": "San Martin",
        "numero": "1234",
        "departamento": "",
        "codigo_postal": "1425",
        "ciudad": "CABA",
        "provincia": "Buenos Aires",
    }


def test_validar_entrega_falla_si_falta_un_obligatorio() -> None:
    with pytest.raises(ErrorDePedido) as error:
        validar_entrega({"direccion": "San Martin"})

    assert "Completa los datos de entrega" in str(error.value)
