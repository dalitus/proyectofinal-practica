"""Tests del detalle de producto (T-031).

Igual que los del catalogo, corren contra `zapateria_test` porque `conftest.py`
apunta el engine del repositorio a la base de test. Cada test arma sus propios
productos y variantes.
"""

from __future__ import annotations

from decimal import Decimal

from sqlmodel import Session

from app.model.categoria_modelo import Categoria
from app.model.product_model import Producto
from app.model.stock_model import Stocks
from app.service.catalogo_servicio import obtener_detalle, talles_por_color


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
    nombre: str = "Zapatilla",
    descripcion: str = "Suela de goma.",
    precio: str = "10000.00",
    marca: str = "Marca",
    activo: bool = True,
    imagen: str | None = "https://example.com/foto.jpg",
    variantes: list[tuple[str, str, int]] | None = None,
) -> Producto:
    """Product with one stock row per ``(color, talle, cantidad)``."""
    producto = Producto(
        nombre=nombre,
        descripcion=descripcion,
        marca=marca,
        precio=Decimal(precio),
        categoria_id=categoria.id,
        activo=activo,
        imagen=imagen,
    )
    session.add(producto)
    session.commit()
    session.refresh(producto)

    for color, talle, cantidad in variantes or [("Negro", "40", 5)]:
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


def test_obtener_detalle_inexistente_e_inactivo(session: Session) -> None:
    categoria = _crear_categoria(session)
    inactivo = _crear_producto(session, categoria, nombre="Descontinuado", activo=False)

    assert obtener_detalle(9999) is None
    assert obtener_detalle(inactivo.id or 0) is None


def test_detalle_arma_los_datos_de_la_pantalla(session: Session) -> None:
    categoria = _crear_categoria(session, "Formal")
    producto = _crear_producto(
        session,
        categoria,
        nombre="Zapato Formal Cuero",
        descripcion="Cuero vacuno.",
        precio="65999.00",
        marca="Hush Puppies",
    )

    detalle = obtener_detalle(producto.id or 0)

    assert detalle is not None
    assert detalle.nombre == "Zapato Formal Cuero"
    assert detalle.marca == "Hush Puppies"
    assert detalle.categoria == "Formal"
    assert detalle.descripcion == "Cuero vacuno."
    assert detalle.precio == "$ 65.999,00"
    assert detalle.total_stock == 5
    assert (detalle.stock_estado, detalle.stock_etiqueta) == (
        "disponible",
        "Disponible",
    )


def test_detalle_sin_imagen_queda_vacio(session: Session) -> None:
    categoria = _crear_categoria(session)
    producto = _crear_producto(session, categoria, imagen=None)

    detalle = obtener_detalle(producto.id or 0)

    assert detalle is not None
    assert detalle.imagen == ""


def test_variantes_y_talles_ordenados(session: Session) -> None:
    categoria = _crear_categoria(session)
    producto = _crear_producto(
        session,
        categoria,
        variantes=[
            ("Negro", "41", 1),
            ("Blanco", "XL", 2),  # talle no numerico: va despues de los numericos
            ("Negro", "40", 4),
            ("Blanco", "40", 0),
        ],
    )

    detalle = obtener_detalle(producto.id or 0)

    assert detalle is not None
    assert detalle.colores == ["Blanco", "Negro"]
    assert detalle.talles == ["40", "41", "XL"]
    assert [(v.color, v.talle, v.cantidad) for v in detalle.variantes] == [
        ("Blanco", "40", 0),
        ("Blanco", "XL", 2),
        ("Negro", "40", 4),
        ("Negro", "41", 1),
    ]


def test_talles_por_color_marca_los_agotados(session: Session) -> None:
    categoria = _crear_categoria(session)
    producto = _crear_producto(
        session,
        categoria,
        variantes=[
            ("Negro", "40", 2),
            ("Negro", "41", 0),
            ("Blanco", "41", 3),
        ],
    )
    detalle = obtener_detalle(producto.id or 0)
    assert detalle is not None

    talles = talles_por_color(detalle)

    assert set(talles) == {"Blanco", "Negro"}
    assert [t["talle"] for t in talles["Negro"]] == ["40", "41"]
    assert [t["agotado"] for t in talles["Negro"]] == [False, True]
    # El talle 40 no existe en blanco: se muestra agotado, no desaparece.
    assert talles["Blanco"] == [
        {"talle": "40", "cantidad": 0, "agotado": True},
        {"talle": "41", "cantidad": 3, "agotado": False},
    ]


def test_producto_agotado_conserva_el_estado_sin_stock(session: Session) -> None:
    categoria = _crear_categoria(session)
    producto = _crear_producto(
        session,
        categoria,
        variantes=[("Negro", "40", 0), ("Negro", "41", 0)],
    )

    detalle = obtener_detalle(producto.id or 0)

    assert detalle is not None
    assert detalle.total_stock == 0
    assert (detalle.stock_estado, detalle.stock_etiqueta) == ("sin_stock", "Sin stock")
