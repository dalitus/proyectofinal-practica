"""Pedidos del admin en ``/admin/pedidos`` (T-051, D-030).

Filtros arriba, tabla abajo y paginacion al pie (design.md 5). La tabla no borra
ni exporta: el admin mira y entra al detalle, donde estan las acciones. Toda la
seccion esta detras de la guarda de rol de ``AdminEstado`` (T-023).
"""

from __future__ import annotations

from typing import Any

import reflex as rx

from app.pages.cuenta_menu import nav_de_cuenta
from app.state.pedidos_admin_estado import PedidosAdminEstado
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


def _estado(pedido: Any) -> rx.Component:
    """Badge with the tone of the state; the label always says the state."""
    return rx.match(
        pedido["estado"],
        ("en espera", Badge(pedido["estado_etiqueta"], tone="info", quiet=True)),
        ("enviado", Badge(pedido["estado_etiqueta"], tone="neutral", quiet=True)),
        ("entregado", Badge(pedido["estado_etiqueta"], tone="success", quiet=True)),
        ("cancelado", Badge(pedido["estado_etiqueta"], tone="danger", quiet=True)),
        Badge(pedido["estado_etiqueta"], tone="neutral", quiet=True),
    )


def _fila(pedido: Any) -> rx.Component:
    return rx.el.tr(
        rx.el.td("#" + pedido["id"].to_string()),
        rx.el.td(pedido["fecha"]),
        rx.el.td(
            rx.el.span(pedido["cliente"], class_name="ui-table__strong"),
            rx.el.span(pedido["email"], class_name="ui-table__muted"),
            class_name="ui-table__stack",
        ),
        rx.el.td(_estado(pedido)),
        rx.el.td(pedido["unidades"], class_name="ui-table__num"),
        rx.el.td(pedido["total"], class_name="ui-table__num ui-table__strong"),
        rx.el.td(
            ButtonLink(
                "Ver",
                href="/admin/pedidos/" + pedido["id"].to_string(),
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
                    rx.el.th("Pedido"),
                    rx.el.th("Fecha"),
                    rx.el.th("Cliente"),
                    rx.el.th("Estado"),
                    rx.el.th("Unidades", class_name="ui-table__num"),
                    rx.el.th("Total", class_name="ui-table__num"),
                    rx.el.th("", class_name="ui-table__actions"),
                )
            ),
            rx.el.tbody(rx.foreach(PedidosAdminEstado.pedidos, _fila)),
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
            opciones=PedidosAdminEstado.filtros,
            label="Estado",
            value=PedidosAdminEstado.filtro,
            on_change=PedidosAdminEstado.filtrar,
            input_id="admin-pedidos-estado",
        ),
        rx.form(
            Input(
                label="Buscar",
                name="busqueda",
                value=PedidosAdminEstado.busqueda,
                on_change=PedidosAdminEstado.escribir_busqueda,
                placeholder="Cliente, email, producto o numero",
                input_id="admin-pedidos-busqueda",
            ),
            rx.el.div(
                Button("Buscar", type="submit"),
                Button(
                    "Limpiar",
                    variant="ghost",
                    on_click=PedidosAdminEstado.limpiar,
                ),
                class_name="ui-admin__filter-actions",
            ),
            on_submit=PedidosAdminEstado.buscar,
            class_name="ui-admin__search",
        ),
        class_name="ui-admin__filters",
    )


def _paginacion() -> rx.Component:
    return rx.el.div(
        Button(
            "Anterior",
            variant="secondary",
            on_click=PedidosAdminEstado.anterior,
            disabled=PedidosAdminEstado.pagina <= 1,
        ),
        rx.el.span(
            "Pagina "
            + PedidosAdminEstado.pagina.to_string()
            + " de "
            + PedidosAdminEstado.total_paginas.to_string(),
            class_name="ui-pagination__info",
        ),
        Button(
            "Siguiente",
            variant="secondary",
            on_click=PedidosAdminEstado.siguiente,
            disabled=PedidosAdminEstado.pagina >= PedidosAdminEstado.total_paginas,
        ),
        class_name="ui-pagination",
    )


def _vacio() -> rx.Component:
    return EmptyState(
        "No hay pedidos con estos filtros",
        "Proba con otro estado, otra busqueda o limpia los filtros.",
        action=Button(
            "Limpiar filtros",
            variant="secondary",
            on_click=PedidosAdminEstado.limpiar,
        ),
    )


def _error() -> rx.Component:
    return rx.el.div(
        Alert(
            title="No pudimos cargar los pedidos",
            description=PedidosAdminEstado.error,
            tone="error",
        ),
        Button(
            "Reintentar",
            variant="secondary",
            on_click=PedidosAdminEstado.reintentar,
        ),
        class_name="ui-stack",
    )


def _contenido() -> Any:
    return rx.cond(
        PedidosAdminEstado.cargando,
        _esqueletos(),
        rx.cond(
            PedidosAdminEstado.error != "",
            _error(),
            rx.cond(
                PedidosAdminEstado.vacio,
                _vacio(),
                rx.el.div(_tabla(), _paginacion(), class_name="ui-stack"),
            ),
        ),
    )


@rx.page(route="/admin/pedidos", title="Pedidos", on_load=PedidosAdminEstado.on_load)
def pedidos_admin_pagina() -> rx.Component:
    return AppShell(
        Container(
            PageHeader("Pedidos", PedidosAdminEstado.resumen),
            AdminTabs(active="pedidos"),
            _filtros(),
            _contenido(),
            class_name="ui-stack",
        ),
        nav=nav_de_cuenta(cart=False),
    )
