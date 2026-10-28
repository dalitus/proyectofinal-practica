"""Catalog rules: pagination, filter options and the view model (D-014).

The state layer calls these functions and stores the result; the page only
renders it. Prices arrive already formatted so no page and no Var repeats the
es-AR rules (D-003, T-032).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from app.model.product_model import Producto
from app.repository import producto_repositorio
from app.service.formato_moneda import formatear_precio

PRODUCTOS_POR_PAGINA = 12
ORDEN_POR_DEFECTO = "nombre"

# Sort key -> label of the select control, in display order.
ORDENES: dict[str, str] = {
    "nombre": "Nombre (A-Z)",
    "precio_asc": "Precio: menor a mayor",
    "precio_desc": "Precio: mayor a menor",
}

# A product is "last units" up to this many total units (design.md 4.3).
UMBRAL_ULTIMAS_UNIDADES = 3


@dataclass(frozen=True)
class ProductoEnCatalogo:
    """One product card, ready to render."""

    id: int
    nombre: str
    marca: str
    categoria: str
    precio: str
    imagen: str
    total_stock: int
    stock_estado: str
    stock_etiqueta: str
    talles: list[str]
    colores: list[str]


@dataclass(frozen=True)
class ResultadoCatalogo:
    productos: list[ProductoEnCatalogo]
    total: int
    pagina: int
    total_paginas: int


@dataclass(frozen=True)
class OpcionesDeFiltro:
    """Options already shaped as ``{"valor", "texto"}`` for the selects."""

    categorias: list[dict[str, str]]
    talles: list[dict[str, str]]
    colores: list[dict[str, str]]


def normalizar_orden(orden: str | None) -> str:
    """Fall back to the default order instead of failing on a stale link."""
    return orden if orden in ORDENES else ORDEN_POR_DEFECTO


def categoria_desde_valor(valor: str | None) -> int | None:
    """Turn the select value into a category id; empty means "all"."""
    if not valor:
        return None
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def _estado_stock(total: int) -> tuple[str, str]:
    """Return (state key, label) for the StockBadge (design.md 4.3).

    The rule lives here and not in the page: "Ultimas 3" is a business message,
    not a formatting detail, and the page would need a numeric comparison on a
    Var typed as ``Any``.
    """
    if total <= 0:
        return "sin_stock", "Sin stock"
    if total <= UMBRAL_ULTIMAS_UNIDADES:
        return "ultimas", f"Ultimas {total}"
    return "disponible", "Disponible"


def _a_producto_en_catalogo(producto: Producto) -> ProductoEnCatalogo:
    variantes = list(producto.stocks)
    total_stock = sum(variante.cantidad_disponible for variante in variantes)
    stock_estado, stock_etiqueta = _estado_stock(total_stock)

    return ProductoEnCatalogo(
        id=producto.id or 0,
        nombre=producto.nombre,
        marca=producto.marca,
        categoria=producto.categoria.nombre if producto.categoria else "",
        precio=formatear_precio(producto.precio),
        imagen=producto.imagen or "",
        total_stock=total_stock,
        stock_estado=stock_estado,
        stock_etiqueta=stock_etiqueta,
        talles=sorted({variante.talle for variante in variantes}),
        colores=sorted({variante.color for variante in variantes}),
    )


def listar_catalogo(
    *,
    busqueda: str = "",
    categoria_id: int | None = None,
    talle: str | None = None,
    color: str | None = None,
    orden: str | None = ORDEN_POR_DEFECTO,
    pagina: int = 1,
) -> ResultadoCatalogo:
    """Return one page of the catalog with the total needed for pagination.

    A page number past the end is clamped to the last page instead of showing an
    empty grid: the buyer changed the filters, not the URL.
    """
    orden_limpio = normalizar_orden(orden)
    texto = (busqueda or "").strip()
    talle_limpio = (talle or "").strip() or None
    color_limpio = (color or "").strip() or None

    filtros = {
        "busqueda": texto,
        "categoria_id": categoria_id,
        "talle": talle_limpio,
        "color": color_limpio,
    }

    total = producto_repositorio.contar_productos(**filtros)
    total_paginas = max(1, math.ceil(total / PRODUCTOS_POR_PAGINA))
    pagina_actual = min(max(1, pagina), total_paginas)

    filas = producto_repositorio.listar_productos(
        **filtros,
        orden=orden_limpio,
        limite=PRODUCTOS_POR_PAGINA,
        offset=(pagina_actual - 1) * PRODUCTOS_POR_PAGINA,
    )

    return ResultadoCatalogo(
        productos=[_a_producto_en_catalogo(fila) for fila in filas],
        total=total,
        pagina=pagina_actual,
        total_paginas=total_paginas,
    )


def opciones_de_filtro() -> OpcionesDeFiltro:
    """Load the categories, sizes and colours for the filter selects."""
    categorias = [
        {"valor": str(categoria.id), "texto": categoria.nombre}
        for categoria in producto_repositorio.listar_categorias()
    ]

    return OpcionesDeFiltro(
        categorias=categorias,
        talles=[
            {"valor": talle, "texto": talle}
            for talle in producto_repositorio.listar_talles()
        ],
        colores=[
            {"valor": color, "texto": color}
            for color in producto_repositorio.listar_colores()
        ],
    )
