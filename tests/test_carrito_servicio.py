"""Tests del carrito (T-040).

Corren contra `zapateria_test`: `conftest.py` apunta el engine del repositorio a
la base de test. Cada test arma su propio comprador, producto y variantes.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from reflex_local_auth.local_auth import LocalUser
from sqlmodel import Session

from app.model.categoria_modelo import Categoria
from app.model.perfil_modelo import UserProfile
from app.model.product_model import Producto
from app.model.stock_model import Stocks
from app.service.carrito_servicio import (
    ErrorDeCarrito,
    agregar,
    cambiar_cantidad,
    quitar,
    vaciar,
    ver_carrito,
)


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


def test_carrito_vacio(session: Session) -> None:
    comprador = _crear_comprador(session)

    carrito = ver_carrito(comprador.id or 0)

    assert carrito.vacio is True
    assert carrito.lineas == []
    assert carrito.total_unidades == 0
    assert carrito.subtotal == "$ 0,00"


def test_agregar_arma_la_linea_con_precio_y_variante(session: Session) -> None:
    comprador = _crear_comprador(session)
    producto, stocks = _crear_producto(session, variantes=[("Blanco", "40", 5)])

    carrito = agregar(comprador.id or 0, stocks[0].id_stock or 0, 2)

    assert carrito.vacio is False
    assert carrito.total_unidades == 2
    linea = carrito.lineas[0]
    assert (linea.nombre, linea.color, linea.talle) == (
        "Zapatilla Running Air",
        "Blanco",
        "40",
    )
    assert linea.variante_id == (stocks[0].id_stock or 0)
    assert linea.producto_id == (producto.id or 0)
    assert linea.cantidad == 2
    assert linea.stock_disponible == 5
    assert linea.precio_unitario == "$ 89.999,00"
    assert linea.subtotal == "$ 179.998,00"
    assert carrito.subtotal == "$ 179.998,00"


def test_agregar_dos_veces_suma_en_la_misma_linea(session: Session) -> None:
    comprador = _crear_comprador(session)
    _, stocks = _crear_producto(session, variantes=[("Blanco", "40", 5)])
    variante_id = stocks[0].id_stock or 0

    agregar(comprador.id or 0, variante_id, 2)
    carrito = agregar(comprador.id or 0, variante_id, 1)

    assert len(carrito.lineas) == 1
    assert carrito.lineas[0].cantidad == 3
    assert carrito.total_unidades == 3


def test_agregar_no_supera_el_stock(session: Session) -> None:
    comprador = _crear_comprador(session)
    _, stocks = _crear_producto(session, variantes=[("Negro", "41", 3)])
    variante_id = stocks[0].id_stock or 0

    agregar(comprador.id or 0, variante_id, 2)

    with pytest.raises(ErrorDeCarrito) as error:
        agregar(comprador.id or 0, variante_id, 2)

    assert "Solo quedan 3 unidades" in str(error.value)
    assert ver_carrito(comprador.id or 0).lineas[0].cantidad == 2


def test_agregar_variante_agotada_o_inexistente(session: Session) -> None:
    comprador = _crear_comprador(session)
    _, stocks = _crear_producto(session, variantes=[("Blanco", "40", 0)])

    with pytest.raises(ErrorDeCarrito) as agotada:
        agregar(comprador.id or 0, stocks[0].id_stock or 0)
    assert "no tiene stock" in str(agotada.value)

    with pytest.raises(ErrorDeCarrito):
        agregar(comprador.id or 0, 99999)

    assert ver_carrito(comprador.id or 0).vacio is True


def test_agregar_producto_inactivo_falla(session: Session) -> None:
    comprador = _crear_comprador(session)
    _, stocks = _crear_producto(session, activo=False)

    with pytest.raises(ErrorDeCarrito) as error:
        agregar(comprador.id or 0, stocks[0].id_stock or 0)

    assert "ya no esta disponible" in str(error.value)


def test_cambiar_cantidad_valida_dueno_y_stock(session: Session) -> None:
    duenio = _crear_comprador(session, "ana@example.com")
    otro = _crear_comprador(session, "beto@example.com")
    _, stocks = _crear_producto(session, variantes=[("Blanco", "40", 4)])
    carrito = agregar(duenio.id or 0, stocks[0].id_stock or 0, 1)
    linea_id = carrito.lineas[0].id

    # Otro comprador no puede tocar una linea ajena.
    with pytest.raises(ErrorDeCarrito):
        cambiar_cantidad(otro.id or 0, linea_id, 2)

    # El duenio si, pero nunca por encima del stock.
    assert cambiar_cantidad(duenio.id or 0, linea_id, 4).lineas[0].cantidad == 4
    with pytest.raises(ErrorDeCarrito):
        cambiar_cantidad(duenio.id or 0, linea_id, 5)


def test_quitar_y_vaciar(session: Session) -> None:
    comprador = _crear_comprador(session)
    _, stocks = _crear_producto(
        session,
        variantes=[("Blanco", "40", 5), ("Negro", "41", 5)],
    )
    usuario_id = comprador.id or 0
    for variante in stocks:
        agregar(usuario_id, variante.id_stock or 0, 1)

    carrito = ver_carrito(usuario_id)
    assert carrito.total_unidades == 2

    carrito = quitar(usuario_id, carrito.lineas[0].id)
    assert carrito.total_unidades == 1

    assert vaciar(usuario_id).vacio is True
    assert ver_carrito(usuario_id).vacio is True


def test_admin_no_puede_agregar_ni_tocar_el_carrito(session: Session) -> None:
    """D-050: the server rejects the admin even if the event is invoked directly."""
    admin = _crear_admin(session)
    _, stocks = _crear_producto(session, variantes=[("Blanco", "40", 5)])
    admin_id = admin.id or 0
    variante_id = stocks[0].id_stock or 0

    with pytest.raises(ErrorDeCarrito) as error:
        agregar(admin_id, variante_id, 1)

    assert str(error.value) == "El administrador no puede comprar."
    assert ver_carrito(admin_id).vacio is True

    with pytest.raises(ErrorDeCarrito):
        cambiar_cantidad(admin_id, 1, 2)

    with pytest.raises(ErrorDeCarrito):
        quitar(admin_id, 1)

    with pytest.raises(ErrorDeCarrito):
        vaciar(admin_id)


def test_subtotal_suma_varias_lineas(session: Session) -> None:
    comprador = _crear_comprador(session)
    _, stocks = _crear_producto(
        session,
        precio="10000.00",
        variantes=[("Blanco", "40", 5), ("Negro", "41", 5)],
    )
    agregar(comprador.id or 0, stocks[0].id_stock or 0, 2)
    carrito = agregar(comprador.id or 0, stocks[1].id_stock or 0, 1)

    assert carrito.total_unidades == 3
    assert carrito.subtotal == "$ 30.000,00"
    assert carrito.subtotal_valor == Decimal("30000.00")
    # Ordenado por nombre y despues por color.
    assert [linea.color for linea in carrito.lineas] == ["Blanco", "Negro"]
