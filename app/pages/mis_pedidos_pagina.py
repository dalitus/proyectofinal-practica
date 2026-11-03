"""Historial de pedidos del comprador en ``/pedidos`` (T-076, D-002).

Solo muestra los pedidos del usuario conectado: el id sale del token en el estado
y el filtro por dueno vive en SQL. La tabla no ofrece acciones: el ciclo de vida
lo mueve el admin (T-044) y el comprador solo consulta el detalle.
"""

from __future__ import annotations

from typing import Any

import reflex as rx

from app.pages.cuenta_menu import nav_de_cuenta
from app.state.mis_pedidos_estado import MisPedidosEstado
from app.ui import (
    Alert,
    AppShell,
    Badge,
    Button,
    ButtonLink,
    Container,
    EmptyState,
    PageHeader,
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
        rx.el.td(_estado(pedido)),
        rx.el.td(pedido["unidades"], class_name="ui-table__num"),
        rx.el.td(pedido["total"], class_name="ui-table__num ui-table__strong"),
        rx.el.td(
            ButtonLink(
                "Ver",
                href="/pedidos/" + pedido["id"].to_string(),
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
                    rx.el.th("Estado"),
                    rx.el.th("Unidades", class_name="ui-table__num"),
                    rx.el.th("Total", class_name="ui-table__num"),
                    rx.el.th("", class_name="ui-table__actions"),
                )
            ),
            rx.el.tbody(rx.foreach(MisPedidosEstado.pedidos, _fila)),
            class_name="ui-table",
        ),
        class_name="ui-table-wrap",
    )


def _paginacion() -> rx.Component:
    return rx.el.div(
        Button(
            "Anterior",
            variant="secondary",
            on_click=MisPedidosEstado.anterior,
            disabled=MisPedidosEstado.pagina <= 1,
        ),
        rx.el.span(
            "Pagina "
            + MisPedidosEstado.pagina.to_string()
            + " de "
            + MisPedidosEstado.total_paginas.to_string(),
            class_name="ui-pagination__info",
        ),
        Button(
            "Siguiente",
            variant="secondary",
            on_click=MisPedidosEstado.siguiente,
            disabled=MisPedidosEstado.pagina >= MisPedidosEstado.total_paginas,
        ),
        class_name="ui-pagination",
    )


def _esqueletos() -> rx.Component:
    return rx.el.div(
        Skeleton("block", height="280px"),
        class_name="ui-table-wrap",
        **{"aria-hidden": "true"},
    )


def _vacio() -> rx.Component:
    return EmptyState(
        "Todavia no hiciste pedidos",
        "Cuando compres, el pedido aparece aca con su estado y su total.",
        action=ButtonLink("Ver el catalogo", href="/"),
    )


def _error() -> rx.Component:
    return rx.el.div(
        Alert(
            title="No pudimos cargar tus pedidos",
            description=MisPedidosEstado.error,
            tone="error",
        ),
        Button(
            "Reintentar",
            variant="secondary",
            on_click=MisPedidosEstado.reintentar,
        ),
        class_name="ui-stack",
    )


def _contenido() -> Any:
    return rx.cond(
        MisPedidosEstado.cargando,
        _esqueletos(),
        rx.cond(
            MisPedidosEstado.error != "",
            _error(),
            rx.cond(
                MisPedidosEstado.vacio,
                _vacio(),
                rx.el.div(
                    _tabla(),
                    rx.cond(
                        MisPedidosEstado.total_paginas > 1,
                        _paginacion(),
                        rx.fragment(),
                    ),
                    class_name="ui-stack",
                ),
            ),
        ),
    )


@rx.page(route="/pedidos", title="Mis pedidos", on_load=MisPedidosEstado.on_load)
def mis_pedidos_pagina() -> rx.Component:
    return AppShell(
        Container(
            PageHeader("Mis pedidos", MisPedidosEstado.resumen),
            _contenido(),
            class_name="ui-stack",
        ),
        nav=nav_de_cuenta(),
    )
