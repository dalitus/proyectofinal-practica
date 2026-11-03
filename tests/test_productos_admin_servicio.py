"""Tests del CRUD de productos del admin (T-050, D-009, D-028, D-049).

Se prueba el servicio, no la pantalla: la transaccion del alta, la validacion de
campos y de variantes, el filtro de inactivos y la auditoria. La subida de
imagen tiene su propio archivo (`test_imagen_servicio.py`).
"""

from __future__ import annotations

import json
import logging
from decimal import Decimal

import pytest
from sqlmodel import Session, select

from app.model.categoria_modelo import Categoria
from app.model.product_model import Producto
from app.model.stock_model import Stocks
from app.service import catalogo_servicio, producto_servicio
from app.service.carrito_servicio import agregar
from app.service.producto_servicio import ErrorDeProducto


def _categoria(session: Session, nombre: str = "Running") -> int:
    categoria = Categoria(nombre=nombre)
    session.add(categoria)
    session.commit()
    session.refresh(categoria)
    return categoria.id or 0


def _datos(categoria_id: int, **cambios: object) -> dict[str, object]:
    datos: dict[str, object] = {
        "nombre": "Zapatilla urbana",
        "marca": "Fermin",
        "precio": "45000",
        "descripcion": "Suela de goma",
        "categoria_id": str(categoria_id),
        "imagen": "",
    }
    datos.update(cambios)
    return datos


def _lineas(caplog: pytest.LogCaptureFixture) -> list[dict]:
    return [
        json.loads(registro.message)
        for registro in caplog.records
        if registro.name == "app.auditoria"
    ]


def _variantes() -> list[dict[str, object]]:
    return [
        {"color": "Negro", "talle": "38", "cantidad": 5},
        {"color": "Negro", "talle": "39", "cantidad": 3},
    ]


def test_crear_producto_guarda_el_producto_y_sus_variantes(session: Session) -> None:
    categoria_id = _categoria(session)

    producto_id = producto_servicio.crear_producto(
        datos=_datos(categoria_id),
        variantes=_variantes(),
        admin_id=1,
    )

    session.commit()
    producto = session.get(Producto, producto_id)
    assert producto is not None
    assert producto.nombre == "Zapatilla urbana"
    assert producto.precio == Decimal("45000")
    assert producto.activo is True

    variantes = session.exec(
        select(Stocks).where(Stocks.producto_id == producto_id)
    ).all()
    assert {(variante.color, variante.talle) for variante in variantes} == {
        ("Negro", "38"),
        ("Negro", "39"),
    }
    assert sum(variante.cantidad_disponible for variante in variantes) == 8


def test_crear_producto_rechaza_variantes_repetidas(session: Session) -> None:
    categoria_id = _categoria(session)

    with pytest.raises(ErrorDeProducto) as error:
        producto_servicio.crear_producto(
            datos=_datos(categoria_id),
            variantes=[
                {"color": "Negro", "talle": "38", "cantidad": 1},
                {"color": "negro", "talle": "38", "cantidad": 2},
            ],
        )

    assert error.value.campo == "variante"
    session.commit()
    assert session.exec(select(Producto)).all() == []
    assert session.exec(select(Stocks)).all() == []


def test_crear_producto_sin_variantes_no_escribe_nada(session: Session) -> None:
    categoria_id = _categoria(session)

    with pytest.raises(ErrorDeProducto):
        producto_servicio.crear_producto(
            datos=_datos(categoria_id),
            variantes=[],
        )

    session.commit()
    assert session.exec(select(Producto)).all() == []


@pytest.mark.parametrize("precio", ["45000,50", "45000.50", "", "0", "abc"])
def test_el_precio_se_valida_en_pesos_enteros(session: Session, precio: str) -> None:
    categoria_id = _categoria(session)

    with pytest.raises(ErrorDeProducto) as error:
        producto_servicio.crear_producto(
            datos=_datos(categoria_id, precio=precio),
            variantes=_variantes(),
        )

    assert error.value.campo == "precio"
    session.commit()
    assert session.exec(select(Producto)).all() == []


def test_el_precio_acepta_separador_de_miles(session: Session) -> None:
    categoria_id = _categoria(session)

    producto_id = producto_servicio.crear_producto(
        datos=_datos(categoria_id, precio="45.000"),
        variantes=_variantes(),
    )

    session.commit()
    producto = session.get(Producto, producto_id)
    assert producto is not None
    assert producto.precio == Decimal("45000")


def test_una_categoria_inexistente_es_un_error_de_campo(session: Session) -> None:
    categoria_id = _categoria(session)

    with pytest.raises(ErrorDeProducto) as error:
        producto_servicio.crear_producto(
            datos=_datos(categoria_id + 100),
            variantes=_variantes(),
        )

    assert error.value.campo == "categoria_id"


def test_el_listado_del_admin_filtra_por_estado_y_busca(session: Session) -> None:
    categoria_id = _categoria(session)
    activo_id = producto_servicio.crear_producto(
        datos=_datos(categoria_id, nombre="Zapatilla activa"),
        variantes=_variantes(),
    )
    inactivo_id = producto_servicio.crear_producto(
        datos=_datos(categoria_id, nombre="Bota guardada"),
        variantes=_variantes(),
    )
    producto_servicio.desactivar_producto(inactivo_id, admin_id=1)

    activos = producto_servicio.listar_para_admin(estado="activos")
    inactivos = producto_servicio.listar_para_admin(estado="inactivos")
    todos = producto_servicio.listar_para_admin(estado="todos")
    buscados = producto_servicio.listar_para_admin(busqueda="bota", estado="todos")

    assert [producto.id for producto in activos.productos] == [activo_id]
    assert [producto.id for producto in inactivos.productos] == [inactivo_id]
    assert todos.total == 2
    assert [producto.id for producto in buscados.productos] == [inactivo_id]
    assert inactivos.productos[0].estado_etiqueta == "Inactivo"


def test_desactivar_lo_saca_del_catalogo_y_reactivar_lo_devuelve(
    session: Session,
) -> None:
    categoria_id = _categoria(session)
    producto_id = producto_servicio.crear_producto(
        datos=_datos(categoria_id),
        variantes=_variantes(),
    )
    assert catalogo_servicio.obtener_detalle(producto_id) is not None

    producto_servicio.desactivar_producto(producto_id, admin_id=1)
    assert catalogo_servicio.obtener_detalle(producto_id) is None

    producto_servicio.reactivar_producto(producto_id, admin_id=1)
    assert catalogo_servicio.obtener_detalle(producto_id) is not None


def test_agregar_variante_rechaza_la_misma_combinacion(session: Session) -> None:
    categoria_id = _categoria(session)
    producto_id = producto_servicio.crear_producto(
        datos=_datos(categoria_id),
        variantes=_variantes(),
    )

    with pytest.raises(ErrorDeProducto) as error:
        producto_servicio.agregar_variante(
            producto_id,
            color="Negro",
            talle="38",
            cantidad=2,
        )
    assert error.value.campo == "variante"

    producto_servicio.agregar_variante(
        producto_id,
        color="Negro",
        talle="40",
        cantidad=4,
    )
    session.commit()
    variantes = session.exec(
        select(Stocks).where(Stocks.producto_id == producto_id)
    ).all()
    assert len(variantes) == 3


def test_actualizar_variante_cambia_el_stock_y_valida_la_combinacion(
    session: Session,
) -> None:
    categoria_id = _categoria(session)
    producto_id = producto_servicio.crear_producto(
        datos=_datos(categoria_id),
        variantes=_variantes(),
    )
    session.commit()
    variantes = session.exec(
        select(Stocks).where(Stocks.producto_id == producto_id).order_by(Stocks.id_stock)
    ).all()
    primera, segunda = variantes

    producto_servicio.actualizar_variante(
        producto_id,
        primera.id_stock or 0,
        color="Negro",
        talle="38",
        cantidad=9,
        admin_id=1,
    )
    session.commit()
    assert session.get(Stocks, primera.id_stock).cantidad_disponible == 9

    with pytest.raises(ErrorDeProducto) as error:
        producto_servicio.actualizar_variante(
            producto_id,
            primera.id_stock or 0,
            color=segunda.color,
            talle=segunda.talle,
            cantidad=1,
        )
    assert error.value.variante_id == primera.id_stock

    with pytest.raises(ErrorDeProducto) as negativo:
        producto_servicio.actualizar_variante(
            producto_id,
            primera.id_stock or 0,
            color="Negro",
            talle="38",
            cantidad=-1,
        )
    assert negativo.value.campo == "cantidad"


def test_eliminar_variante_con_carrito_falla_y_sin_uso_la_borra(
    session: Session,
) -> None:
    categoria_id = _categoria(session)
    producto_id = producto_servicio.crear_producto(
        datos=_datos(categoria_id),
        variantes=_variantes(),
    )
    session.commit()
    variantes = session.exec(
        select(Stocks).where(Stocks.producto_id == producto_id).order_by(Stocks.id_stock)
    ).all()
    primera_id = variantes[0].id_stock or 0
    segunda_id = variantes[1].id_stock or 0
    # La borra el servicio en otra sesion: si quedan cargadas aca, el commit
    # intenta refrescarlas y SQLAlchemy avisa que la fila ya no existe.
    for variante in variantes:
        session.expunge(variante)

    from reflex_local_auth.local_auth import LocalUser

    usuario = LocalUser(
        username="comprador@example.com",
        password_hash=LocalUser.hash_password("secreto123"),
        enabled=True,
    )
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    agregar(usuario.id or 0, primera_id, 1)

    with pytest.raises(ErrorDeProducto):
        producto_servicio.eliminar_variante(producto_id, primera_id, admin_id=1)

    producto_servicio.eliminar_variante(producto_id, segunda_id, admin_id=1)
    session.commit()
    assert (
        session.exec(select(Stocks.id_stock).where(Stocks.id_stock == primera_id)).first()
        is not None
    )
    assert (
        session.exec(select(Stocks.id_stock).where(Stocks.id_stock == segunda_id)).first()
        is None
    )


def test_cada_operacion_confirmada_deja_su_linea_de_auditoria(
    session: Session,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="app.auditoria")
    categoria_id = _categoria(session)

    producto_id = producto_servicio.crear_producto(
        datos=_datos(categoria_id),
        variantes=_variantes(),
        admin_id=5,
    )
    producto_servicio.actualizar_producto(
        producto_id,
        datos=_datos(categoria_id, nombre="Zapatilla editada"),
        admin_id=5,
    )
    producto_servicio.agregar_variante(
        producto_id, color="Gris", talle="41", cantidad=2, admin_id=5
    )
    producto_servicio.desactivar_producto(producto_id, admin_id=5)

    acciones = [linea["accion"] for linea in _lineas(caplog)]
    assert acciones == [
        "crear_producto",
        "actualizar_producto",
        "agregar_variante",
        "desactivar_producto",
    ]
    assert all(linea["admin_id"] == 5 for linea in _lineas(caplog))


def test_una_operacion_rechazada_no_deja_rastro(
    session: Session,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="app.auditoria")
    categoria_id = _categoria(session)

    with pytest.raises(ErrorDeProducto):
        producto_servicio.crear_producto(
            datos=_datos(categoria_id, precio="cero"),
            variantes=_variantes(),
            admin_id=5,
        )

    assert _lineas(caplog) == []
