"""Tests del catalogo: formato, filtros, orden, paginacion y stock (T-030, T-033).

Corren contra `zapateria_test` gracias a `conftest.py`, que apunta el engine del
repositorio a la base de test. Los datos de cada test se crean aca mismo y la
fixture `session` vacia las tablas antes de empezar.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from sqlmodel import Session

from app.model.categoria_modelo import Categoria
from app.model.producto_modelo import Producto
from app.model.variante_modelo import Stocks
from app.service.catalogo_servicio import (
    PRODUCTOS_POR_PAGINA,
    categoria_desde_valor,
    listar_catalogo,
    normalizar_orden,
    opciones_de_filtro,
)
from app.service.formato_moneda import formatear_precio


def _crear_categoria(session: Session, nombre: str = "Running") -> Categoria:
    categoria = Categoria(nombre=nombre)
    session.add(categoria)
    session.commit()
    session.refresh(categoria)
    return categoria


def _crear_producto(
    session: Session,
    categoria: Categoria,
    *,
    nombre: str,
    precio: str = "10000.00",
    marca: str = "Marca",
    activo: bool = True,
    cantidad: int = 5,
    color: str = "Negro",
    talle: str = "40",
    imagen: str | None = "https://example.com/foto.jpg",
) -> Producto:
    producto = Producto(
        nombre=nombre,
        marca=marca,
        precio=Decimal(precio),
        categoria_id=categoria.id,
        activo=activo,
        imagen=imagen,
    )
    session.add(producto)
    session.commit()
    session.refresh(producto)

    session.add(
        Stocks(
            producto_id=producto.id,
            color=color,
            talle=talle,
            cantidad_disponible=cantidad,
        )
    )
    session.commit()
    return producto


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        (Decimal("89999"), "$ 89.999,00"),
        (Decimal("1234.5"), "$ 1.234,50"),
        (Decimal("1234.567"), "$ 1.234,57"),
        (Decimal("99999.999"), "$ 100.000,00"),
        ("9999999.99", "$ 9.999.999,99"),
        (0, "$ 0,00"),
        (None, ""),
        ("", ""),
        ("no-es-un-precio", ""),
    ],
)
def test_formatear_precio(valor: object, esperado: str) -> None:
    """El mismo helper para todas las pantallas (D-003, T-032)."""
    assert formatear_precio(valor) == esperado


def test_normalizar_orden_cae_en_el_default() -> None:
    assert normalizar_orden("precio_asc") == "precio_asc"
    assert normalizar_orden("cualquier-cosa") == "nombre"
    assert normalizar_orden(None) == "nombre"


def test_categoria_desde_valor() -> None:
    assert categoria_desde_valor("3") == 3
    assert categoria_desde_valor("") is None
    assert categoria_desde_valor(None) is None
    assert categoria_desde_valor("no-es-un-id") is None


def test_solo_muestra_productos_activos(session: Session) -> None:
    categoria = _crear_categoria(session)
    _crear_producto(session, categoria, nombre="Activo")
    _crear_producto(session, categoria, nombre="Descontinuado", activo=False)

    resultado = listar_catalogo()

    assert resultado.total == 1
    assert [p.nombre for p in resultado.productos] == ["Activo"]


def test_busqueda_por_nombre_y_marca(session: Session) -> None:
    categoria = _crear_categoria(session)
    _crear_producto(session, categoria, nombre="Zapatilla Running Air", marca="Nike")
    _crear_producto(session, categoria, nombre="Zapato Formal", marca="Hush Puppies")

    assert [p.nombre for p in listar_catalogo(busqueda="running").productos] == [
        "Zapatilla Running Air"
    ]
    assert [p.nombre for p in listar_catalogo(busqueda="hush").productos] == [
        "Zapato Formal"
    ]
    assert listar_catalogo(busqueda="   ").total == 2
    assert listar_catalogo(busqueda="no-existe").total == 0


def test_filtros_de_categoria_talle_y_color_combinados(session: Session) -> None:
    running = _crear_categoria(session, "Running")
    formal = _crear_categoria(session, "Formal")

    _crear_producto(
        session,
        running,
        nombre="Running Negra 40",
        color="Negro",
        talle="40",
    )
    _crear_producto(
        session,
        running,
        nombre="Running Blanca 42",
        color="Blanco",
        talle="42",
    )
    _crear_producto(
        session,
        formal,
        nombre="Zapato Negro 40",
        color="Negro",
        talle="40",
    )

    assert listar_catalogo(categoria_id=formal.id).total == 1
    assert listar_catalogo(talle="42").total == 1
    assert listar_catalogo(color="Negro").total == 2

    combinado = listar_catalogo(
        categoria_id=running.id,
        color="Negro",
        talle="40",
    )
    assert [p.nombre for p in combinado.productos] == ["Running Negra 40"]


def test_orden_por_nombre_y_precio(session: Session) -> None:
    categoria = _crear_categoria(session)
    _crear_producto(session, categoria, nombre="B Producto", precio="200")
    _crear_producto(session, categoria, nombre="A Producto", precio="300")
    _crear_producto(session, categoria, nombre="C Producto", precio="100")

    assert [p.nombre for p in listar_catalogo().productos] == [
        "A Producto",
        "B Producto",
        "C Producto",
    ]
    assert [p.nombre for p in listar_catalogo(orden="precio_asc").productos] == [
        "C Producto",
        "B Producto",
        "A Producto",
    ]
    assert [p.nombre for p in listar_catalogo(orden="precio_desc").productos] == [
        "A Producto",
        "B Producto",
        "C Producto",
    ]


def test_paginacion_de_doce_y_limites(session: Session) -> None:
    categoria = _crear_categoria(session)
    for indice in range(PRODUCTOS_POR_PAGINA + 1):
        _crear_producto(session, categoria, nombre=f"Producto {indice:02d}")

    primera = listar_catalogo(pagina=1)
    segunda = listar_catalogo(pagina=2)

    assert primera.total == PRODUCTOS_POR_PAGINA + 1
    assert primera.total_paginas == 2
    assert len(primera.productos) == PRODUCTOS_POR_PAGINA
    assert len(segunda.productos) == 1

    # Una pagina fuera de rango se recorta al ultimo tramo en vez de quedar vacia.
    pasada = listar_catalogo(pagina=99)
    assert pasada.pagina == 2
    assert len(pasada.productos) == 1

    cero = listar_catalogo(pagina=0)
    assert cero.pagina == 1


def test_estado_de_stock(session: Session) -> None:
    categoria = _crear_categoria(session)
    con_stock = _crear_producto(session, categoria, nombre="Con stock", cantidad=10)
    ultimas = _crear_producto(session, categoria, nombre="Ultimas", cantidad=3)
    agotado = _crear_producto(session, categoria, nombre="Agotado", cantidad=0)

    estados = {p.id: (p.stock_estado, p.stock_etiqueta) for p in listar_catalogo().productos}

    assert estados[con_stock.id] == ("disponible", "Disponible")
    assert estados[ultimas.id] == ("ultimas", "Ultimas 3")
    assert estados[agotado.id] == ("sin_stock", "Sin stock")


def test_producto_sin_imagen_queda_vacio(session: Session) -> None:
    categoria = _crear_categoria(session)
    _crear_producto(session, categoria, nombre="Sin foto", imagen=None)

    assert listar_catalogo().productos[0].imagen == ""


def test_opciones_de_filtro(session: Session) -> None:
    running = _crear_categoria(session, "Running")
    formal = _crear_categoria(session, "Formal")
    _crear_producto(session, running, nombre="A", talle="40", color="Negro")
    _crear_producto(session, formal, nombre="B", talle="42", color="Blanco")
    # Una categoria sin productos activos no se ofrece como filtro.
    vacia = _crear_categoria(session, "Vacia")
    _crear_producto(session, vacia, nombre="Inactivo", activo=False)

    opciones = opciones_de_filtro()

    assert [c["texto"] for c in opciones.categorias] == ["Formal", "Running"]
    assert [t["valor"] for t in opciones.talles] == ["40", "42"]
    assert [c["valor"] for c in opciones.colores] == ["Blanco", "Negro"]
