"""Productos del admin en ``/admin/productos`` (T-050, D-028, D-049).

Filtros arriba, tabla abajo y paginacion al pie (design.md 5). La tabla muestra
activos e inactivos segun el filtro y no borra nada: el detalle es donde se
edita, se dan de baja las variantes y se desactiva el producto.

Toda la seccion esta detras de la guarda de rol de ``AdminEstado`` (T-023).
"""

from __future__ import annotations

from typing import Any

import reflex as rx

from app.pages.cuenta_menu import nav_de_cuenta
from app.state.productos_admin_estado import ProductosAdminEstado
from app.ui import (
    AdminTabs,
    Alert,
    AppShell,
    Badge,
    Button,
    ButtonLink,
    Container,
    EmptyState,
    Input,
    PageHeader,
    Select,
    Skeleton,
)

ESQUELETOS_AL_CARGAR = 5


def _estado(producto: Any) -> rx.Component:
    return rx.cond(
        producto["activo"],
        Badge("Activo", tone="success", quiet=True),
        Badge("Inactivo", tone="neutral", quiet=True),
    )


def _fila(producto: Any) -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            rx.el.span(producto["nombre"], class_name="ui-table__strong"),
            rx.el.span(producto["marca"], class_name="ui-table__muted"),
            class_name="ui-table__stack",
        ),
        rx.el.td(producto["categoria"]),
        rx.el.td(producto["precio"], class_name="ui-table__num"),
        rx.el.td(producto["variantes"], class_name="ui-table__num"),
        rx.el.td(producto["stock"], class_name="ui-table__num"),
        rx.el.td(_estado(producto)),
        rx.el.td(
            ButtonLink(
                "Ver",
                href="/admin/productos/" + producto["id"].to_string(),
                variant="ghost",
            ),
            class_name="ui-table__actions",
        ),
        class_name="ui-table__row",
    )


def _tabla() -> rx.Component:
    return rx.el.div(
        rx.el.table(
            rx.el.thead(
                rx.el.tr(
                    rx.el.th("Producto"),
                    rx.el.th("Categoria"),
                    rx.el.th("Precio", class_name="ui-table__num"),
                    rx.el.th("Variantes", class_name="ui-table__num"),
                    rx.el.th("Stock", class_name="ui-table__num"),
                    rx.el.th("Estado"),
                    rx.el.th("", class_name="ui-table__actions"),
                )
            ),
            rx.el.tbody(rx.foreach(ProductosAdminEstado.productos, _fila)),
            class_name="ui-table",
        ),
        class_name="ui-table-wrap",
    )


def _esqueletos() -> rx.Component:
    return rx.el.div(
        Skeleton("block", height="280px"),
        class_name="ui-table-wrap",
        **{"aria-hidden": "true"},
    )


def _filtros() -> rx.Component:
    return rx.el.div(
        Select(
            opciones=ProductosAdminEstado.filtros,
            label="Estado",
            value=ProductosAdminEstado.filtro,
            on_change=ProductosAdminEstado.filtrar,
            input_id="admin-productos-estado",
        ),
        rx.form(
            Input(
                label="Buscar",
                name="busqueda",
                value=ProductosAdminEstado.busqueda,
                on_change=ProductosAdminEstado.escribir_busqueda,
                placeholder="Nombre o marca",
                input_id="admin-productos-busqueda",
            ),
            rx.el.div(
                Button("Buscar", type="submit"),
                Button(
                    "Limpiar",
                    variant="ghost",
                    on_click=ProductosAdminEstado.limpiar,
                ),
                class_name="ui-admin__filter-actions",
            ),
            on_submit=ProductosAdminEstado.buscar,
            class_name="ui-admin__search",
        ),
        class_name="ui-admin__filters",
    )


def _paginacion() -> rx.Component:
    return rx.el.div(
        Button(
            "Anterior",
            variant="secondary",
            on_click=ProductosAdminEstado.anterior,
            disabled=ProductosAdminEstado.pagina <= 1,
        ),
        rx.el.span(
            "Pagina "
            + ProductosAdminEstado.pagina.to_string()
            + " de "
            + ProductosAdminEstado.total_paginas.to_string(),
            class_name="ui-pagination__info",
        ),
        Button(
            "Siguiente",
            variant="secondary",
            on_click=ProductosAdminEstado.siguiente,
            disabled=ProductosAdminEstado.pagina >= ProductosAdminEstado.total_paginas,
        ),
        class_name="ui-pagination",
    )


def _vacio() -> rx.Component:
    return EmptyState(
        "No hay productos con estos filtros",
        "Proba con otro estado, otra busqueda o limpia los filtros.",
        action=Button(
            "Limpiar filtros",
            variant="secondary",
            on_click=ProductosAdminEstado.limpiar,
        ),
    )


def _error() -> rx.Component:
    return rx.el.div(
        Alert(
            title="No pudimos cargar los productos",
            description=ProductosAdminEstado.error,
            tone="error",
        ),
        Button(
            "Reintentar",
            variant="secondary",
            on_click=ProductosAdminEstado.reintentar,
        ),
        class_name="ui-stack",
    )


def _contenido() -> Any:
    return rx.cond(
        ProductosAdminEstado.cargando,
        _esqueletos(),
        rx.cond(
            ProductosAdminEstado.error != "",
            _error(),
            rx.cond(
                ProductosAdminEstado.vacio,
                _vacio(),
                rx.el.div(_tabla(), _paginacion(), class_name="ui-stack"),
            ),
        ),
    )


@rx.page(
    route="/admin/productos",
    title="Productos",
    on_load=ProductosAdminEstado.on_load,
)
def productos_admin_pagina() -> rx.Component:
    return AppShell(
        Container(
            PageHeader(
                "Productos",
                ProductosAdminEstado.resumen,
                actions=ButtonLink("Nuevo producto", href="/admin/productos/nuevo"),
            ),
            AdminTabs(active="productos"),
            _filtros(),
            _contenido(),
            class_name="ui-stack",
        ),
        nav=nav_de_cuenta(cart=False),
    )
