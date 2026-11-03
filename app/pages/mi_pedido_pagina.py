"""Detalle de un pedido propio en ``/pedidos/[pedido_id]`` (T-076, D-002).

La ruta lleva el id y la consulta filtra por dueno: un pedido ajeno se muestra
como inexistente, no como error de permisos. El comprador no cambia estados; solo
lee lo que el admin movio (T-044).
"""

from __future__ import annotations

from typing import Any

import reflex as rx

from app.pages.cuenta_menu import nav_de_cuenta
from app.state.mis_pedidos_estado import MiPedidoEstado
from app.ui import (
    Alert,
    AppShell,
    Badge,
    Button,
    ButtonLink,
    Card,
    Container,
    EmptyState,
    PageHeader,
    Skeleton,
)


def _volver() -> rx.Component:
    return rx.el.a("Volver a mis pedidos", href="/pedidos", class_name="ui-back")


def _estado() -> rx.Component:
    return rx.match(
        MiPedidoEstado.pedido["estado"],
        ("en espera", Badge(MiPedidoEstado.pedido["estado_etiqueta"], tone="info", quiet=True)),
        ("enviado", Badge(MiPedidoEstado.pedido["estado_etiqueta"], tone="neutral", quiet=True)),
        ("entregado", Badge(MiPedidoEstado.pedido["estado_etiqueta"], tone="success", quiet=True)),
        ("cancelado", Badge(MiPedidoEstado.pedido["estado_etiqueta"], tone="danger", quiet=True)),
        Badge(MiPedidoEstado.pedido["estado_etiqueta"], tone="neutral", quiet=True),
    )


def _datos() -> rx.Component:
    return Card(
        rx.el.div(
            rx.el.div(
                rx.el.span("Fecha", class_name="ui-text ui-text--muted ui-text--small"),
                rx.el.span(MiPedidoEstado.pedido["fecha"]),
                class_name="ui-admin__field",
            ),
            rx.el.div(
                rx.el.span("Estado", class_name="ui-text ui-text--muted ui-text--small"),
                _estado(),
                class_name="ui-admin__field",
            ),
            rx.el.div(
                rx.el.span("Entrega", class_name="ui-text ui-text--muted ui-text--small"),
                rx.el.span(MiPedidoEstado.pedido["envio"]),
                class_name="ui-admin__field",
            ),
            class_name="ui-admin__data",
        ),
        class_name="ui-stack",
    )


def _linea(linea: Any) -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            rx.el.span(linea["producto"], class_name="ui-table__strong"),
            rx.el.span(
                "Color "
                + linea["color"].to_string(use_json=False)
                + " - Talle "
                + linea["talle"].to_string(use_json=False),
                class_name="ui-table__muted",
            ),
            class_name="ui-table__stack",
        ),
        rx.el.td(linea["cantidad"], class_name="ui-table__num"),
        rx.el.td(linea["precio_unitario"], class_name="ui-table__num"),
        rx.el.td(linea["subtotal"], class_name="ui-table__num ui-table__strong"),
    )


def _lineas() -> rx.Component:
    return rx.el.div(
        rx.el.table(
            rx.el.thead(
                rx.el.tr(
                    rx.el.th("Producto"),
                    rx.el.th("Cantidad", class_name="ui-table__num"),
                    rx.el.th("Precio", class_name="ui-table__num"),
                    rx.el.th("Subtotal", class_name="ui-table__num"),
                )
            ),
            rx.el.tbody(rx.foreach(MiPedidoEstado.lineas, _linea)),
            class_name="ui-table",
        ),
        rx.el.div(
            rx.el.span(
                MiPedidoEstado.unidades_texto,
                class_name="ui-text ui-text--muted ui-text--small",
            ),
            rx.el.span(
                "Total " + MiPedidoEstado.pedido["total"].to_string(use_json=False),
                class_name="ui-admin__total",
            ),
            class_name="ui-admin__totals",
        ),
        class_name="ui-table-wrap ui-stack",
    )


def _esqueletos() -> rx.Component:
    return rx.el.div(
        Skeleton("block", height="160px"),
        Skeleton("block", height="220px"),
        class_name="ui-stack",
        **{"aria-hidden": "true"},
    )


def _no_encontrado() -> rx.Component:
    return EmptyState(
        "Ese pedido no existe",
        "Puede que sea de otra cuenta o que el link este mal.",
        action=ButtonLink("Ver mis pedidos", href="/pedidos"),
    )


def _error() -> rx.Component:
    return rx.el.div(
        Alert(
            title="No pudimos cargar el pedido",
            description=MiPedidoEstado.error,
            tone="error",
        ),
        Button(
            "Reintentar",
            variant="secondary",
            on_click=MiPedidoEstado.reintentar,
        ),
        class_name="ui-stack",
    )


def _contenido() -> Any:
    return rx.cond(
        MiPedidoEstado.cargando,
        _esqueletos(),
        rx.cond(
            MiPedidoEstado.error != "",
            _error(),
            rx.cond(
                MiPedidoEstado.no_encontrado,
                _no_encontrado(),
                rx.el.div(_datos(), _lineas(), class_name="ui-stack"),
            ),
        ),
    )


@rx.page(
    route="/pedidos/[pedido_id]",
    title="Mi pedido",
    on_load=MiPedidoEstado.on_load,
)
def mi_pedido_pagina() -> rx.Component:
    return AppShell(
        Container(
            _volver(),
            PageHeader(MiPedidoEstado.titulo),
            _contenido(),
            class_name="ui-stack",
        ),
        nav=nav_de_cuenta(),
    )
