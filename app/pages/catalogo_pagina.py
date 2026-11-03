"""Catalogo en la raiz (D-024): listado, filtros y paginacion (T-030, T-033).

Solo composicion: los primitivos y las clases vienen de ``app.ui``, el estado
entrega los precios ya formateados y aca no hay un solo color, sombra o tamano
suelto. La pantalla tiene un proposito: elegir producto (design.md 1).
"""

from __future__ import annotations

from typing import Any

import reflex as rx

from app.pages.cuenta_menu import nav_de_cuenta
from app.service.catalogo_servicio import ORDENES
from app.state.catalogo_estado import CatalogoEstado
from app.ui import (
    Alert,
    AppShell,
    Badge,
    Button,
    Card,
    Container,
    EmptyState,
    Input,
    PageHeader,
    Select,
    Skeleton,
    src_de_imagen,
)

# design.md 4.3: the grid renders 8 skeletons while loading.
ESQUELETOS_AL_CARGAR = 8


def _contador() -> Any:
    """Result counter for the page header (design.md 4.3)."""
    return rx.cond(
        CatalogoEstado.cargando,
        "Cargando productos",
        rx.cond(
            CatalogoEstado.total == 1,
            "1 producto",
            CatalogoEstado.total.to_string() + " productos",
        ),
    )


def _filtros() -> rx.Component:
    """Search + category + size + colour + order, in one row from 1024px up."""
    return rx.form(
        rx.el.div(
            Input(
                label="Buscar",
                placeholder="Nombre o marca",
                name="busqueda",
                value=CatalogoEstado.busqueda,
                on_change=CatalogoEstado.set_busqueda,
            ),
            Select(
                ("", "Todas"),
                label="Categoria",
                name="categoria",
                value=CatalogoEstado.categoria,
                on_change=CatalogoEstado.set_categoria,
                opciones=CatalogoEstado.categorias,
            ),
            Select(
                ("", "Todos"),
                label="Talle",
                name="talle",
                value=CatalogoEstado.talle,
                on_change=CatalogoEstado.set_talle,
                opciones=CatalogoEstado.talles,
            ),
            Select(
                ("", "Todos"),
                label="Color",
                name="color",
                value=CatalogoEstado.color,
                on_change=CatalogoEstado.set_color,
                opciones=CatalogoEstado.colores,
            ),
            Select(
                *ORDENES.items(),
                label="Orden",
                name="orden",
                value=CatalogoEstado.orden,
                on_change=CatalogoEstado.set_orden,
            ),
            class_name="ui-filters__fields",
        ),
        rx.el.div(
            rx.cond(
                CatalogoEstado.hay_filtros,
                Button(
                    "Limpiar filtros",
                    variant="ghost",
                    on_click=CatalogoEstado.limpiar_filtros,
                ),
                rx.fragment(),
            ),
            Button("Buscar", type="submit", loading=CatalogoEstado.cargando),
            class_name="ui-filters__actions",
        ),
        class_name="ui-filters",
        on_submit=CatalogoEstado.buscar,
    )


def _estado_de_stock(producto: Any) -> rx.Component:
    """Disponible / Ultimas N / Sin stock, with the tone only in the dot."""
    return rx.match(
        producto["stock_estado"],
        ("sin_stock", Badge("Sin stock", tone="danger", quiet=True)),
        ("ultimas", Badge(producto["stock_etiqueta"], tone="info", quiet=True)),
        Badge("Disponible", tone="success", quiet=True),
    )


def _tarjeta(producto: Any) -> rx.Component:
    """ProductCard: 3:4 image, brand, name, final price and stock (design.md 4.3).

    The card itself is the link to ``/producto/[id]`` (D-024): a click anywhere
    on it opens the detail, and the browser still gets a real anchor.
    """
    return rx.link(
        Card(
            rx.el.div(
                rx.cond(
                    producto["imagen"] != "",
                    rx.image(
                        src=src_de_imagen(producto["imagen"]),
                        alt=producto["nombre"],
                        loading="lazy",
                        class_name="ui-product__image",
                    ),
                    rx.el.div("Sin imagen", class_name="ui-product__placeholder"),
                ),
                class_name="ui-product__media",
            ),
            rx.el.div(
                rx.cond(
                    producto["marca"] != "",
                    rx.el.p(
                        producto["marca"],
                        class_name="ui-text ui-text--muted ui-text--small",
                    ),
                    rx.fragment(),
                ),
                rx.el.h2(producto["nombre"], class_name="ui-product__name"),
                rx.el.p(producto["precio"], class_name="ui-product__price"),
                _estado_de_stock(producto),
                class_name="ui-product__body",
            ),
            class_name="ui-product",
        ),
        href="/producto/" + producto["id"].to_string(),
        class_name="ui-product-link",
    )


def _esqueletos() -> rx.Component:
    return rx.el.div(
        *[Skeleton("card") for _ in range(ESQUELETOS_AL_CARGAR)],
        class_name="ui-grid",
        **{"aria-hidden": "true"},
    )


def _error() -> rx.Component:
    return rx.el.div(
        Alert(
            title="No pudimos cargar el catalogo",
            description=CatalogoEstado.error,
            tone="error",
        ),
        Button(
            "Reintentar",
            variant="secondary",
            on_click=CatalogoEstado.reintentar,
        ),
        class_name="ui-stack",
    )


def _vacio() -> rx.Component:
    """Two different empty states: no matches is not the same as an empty shop."""
    return rx.cond(
        CatalogoEstado.hay_filtros,
        EmptyState(
            "No encontramos productos con esos filtros",
            "Proba con otra busqueda, otro talle u otro color.",
            action=Button(
                "Limpiar filtros",
                variant="secondary",
                on_click=CatalogoEstado.limpiar_filtros,
            ),
        ),
        EmptyState(
            "Todavia no hay productos",
            "Cuando el administrador cargue el catalogo, los productos van a aparecer aca.",
        ),
    )


def _listado() -> rx.Component:
    return rx.cond(
        CatalogoEstado.cargando,
        _esqueletos(),
        rx.cond(
            CatalogoEstado.error != "",
            _error(),
            rx.cond(
                CatalogoEstado.productos.length() == 0,
                _vacio(),
                rx.el.div(
                    rx.foreach(CatalogoEstado.productos, _tarjeta),
                    class_name="ui-grid",
                ),
            ),
        ),
    )


def _paginacion() -> rx.Component:
    return rx.cond(
        CatalogoEstado.total_paginas > 1,
        rx.el.nav(
            Button(
                "Anterior",
                variant="secondary",
                disabled=CatalogoEstado.pagina <= 1,
                on_click=CatalogoEstado.pagina_anterior,
            ),
            rx.el.span(
                "Pagina ",
                CatalogoEstado.pagina,
                " de ",
                CatalogoEstado.total_paginas,
                class_name="ui-text ui-text--muted",
            ),
            Button(
                "Siguiente",
                variant="secondary",
                disabled=CatalogoEstado.pagina >= CatalogoEstado.total_paginas,
                on_click=CatalogoEstado.pagina_siguiente,
            ),
            class_name="ui-pagination",
            **{"aria-label": "Paginacion del catalogo"},
        ),
        rx.fragment(),
    )


@rx.page(route="/", title="Catalogo", on_load=CatalogoEstado.on_load)
def catalogo_pagina() -> rx.Component:
    return AppShell(
        Container(
            PageHeader("Catalogo", _contador()),
            rx.el.p(
                _contador(),
                class_name="ui-visually-hidden",
                role="status",
                **{"aria-live": "polite"},
            ),
            _filtros(),
            _listado(),
            _paginacion(),
            class_name="ui-stack",
        ),
        nav=nav_de_cuenta(),
    )
