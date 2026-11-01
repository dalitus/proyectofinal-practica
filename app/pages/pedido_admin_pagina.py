"""Detalle de un pedido del admin en ``/admin/pedidos/[pedido_id]`` (T-051, D-030).

La ruta lleva el id, asi que recargar o abrir el link directo muestra el mismo
pedido. Las acciones salen del ciclo de vida (T-044): la pagina no inventa una
transicion, pinta las que el servicio permite y cada una pide confirmacion
(design.md 6, D-010).
"""

from __future__ import annotations

from typing import Any

import reflex as rx

from app.pages.cuenta_menu import nav_de_cuenta
from app.state.pedidos_admin_estado import PedidoAdminEstado
from app.ui import (
    AdminTabs,
    Alert,
    AppShell,
    Badge,
    Button,
    ButtonLink,
    Card,
    ConfirmDialog,
    Container,
    EmptyState,
    PageHeader,
    Skeleton,
)


def _volver() -> rx.Component:
    return rx.el.a("Volver a pedidos", href="/admin/pedidos", class_name="ui-back")


def _estado() -> rx.Component:
    return rx.match(
        PedidoAdminEstado.pedido["estado"],
        ("en espera", Badge(PedidoAdminEstado.pedido["estado_etiqueta"], tone="info", quiet=True)),
        ("enviado", Badge(PedidoAdminEstado.pedido["estado_etiqueta"], tone="neutral", quiet=True)),
        ("entregado", Badge(PedidoAdminEstado.pedido["estado_etiqueta"], tone="success", quiet=True)),
        ("cancelado", Badge(PedidoAdminEstado.pedido["estado_etiqueta"], tone="danger", quiet=True)),
        Badge(PedidoAdminEstado.pedido["estado_etiqueta"], tone="neutral", quiet=True),
    )


def _datos() -> rx.Component:
    return Card(
        rx.el.div(
            rx.el.div(
                rx.el.span("Cliente", class_name="ui-text ui-text--muted ui-text--small"),
                rx.el.span(PedidoAdminEstado.pedido["cliente"], class_name="ui-table__strong"),
                rx.el.span(PedidoAdminEstado.pedido["email"], class_name="ui-table__muted"),
                class_name="ui-admin__field",
            ),
            rx.el.div(
                rx.el.span("Fecha", class_name="ui-text ui-text--muted ui-text--small"),
                rx.el.span(PedidoAdminEstado.pedido["fecha"]),
                class_name="ui-admin__field",
            ),
            rx.el.div(
                rx.el.span("Estado", class_name="ui-text ui-text--muted ui-text--small"),
                _estado(),
                class_name="ui-admin__field",
            ),
            rx.el.div(
                rx.el.span("Entrega", class_name="ui-text ui-text--muted ui-text--small"),
                rx.el.span(PedidoAdminEstado.pedido["envio"]),
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
            rx.el.tbody(rx.foreach(PedidoAdminEstado.lineas, _linea)),
            class_name="ui-table",
        ),
        rx.el.div(
            rx.el.span(
                PedidoAdminEstado.unidades_texto,
                class_name="ui-text ui-text--muted ui-text--small",
            ),
            rx.el.span(
                "Total " + PedidoAdminEstado.pedido["total"].to_string(use_json=False),
                class_name="ui-admin__total",
            ),
            class_name="ui-admin__totals",
        ),
        class_name="ui-table-wrap ui-stack",
    )


def _accion(opcion: Any) -> rx.Component:
    """One allowed transition: cancel is red, the rest are secondary."""
    return rx.cond(
        opcion["valor"] == "cancelado",
        ConfirmDialog(
            trigger=Button("Cancelar pedido", variant="danger"),
            title="Cancelar el pedido",
            description=(
                "Se repone el stock de todas las lineas y el pedido queda "
                "cancelado. Esta accion no se puede deshacer."
            ),
            confirm_label="Cancelar pedido",
            cancel_label="Volver",
            on_confirm=PedidoAdminEstado.cambiar(opcion["valor"]),
        ),
        ConfirmDialog(
            trigger=Button(
                "Marcar como " + opcion["texto"].to_string(use_json=False).lower(),
                variant="secondary",
            ),
            title="Cambiar el estado del pedido",
            description=(
                "El pedido #"
                + PedidoAdminEstado.pedido_id.to_string()
                + " pasa a "
                + opcion["texto"].to_string(use_json=False).lower()
                + "."
            ),
            confirm_label="Cambiar estado",
            on_confirm=PedidoAdminEstado.cambiar(opcion["valor"]),
        ),
    )


def _acciones() -> rx.Component:
    return Card(
        rx.el.h2("Cambiar estado", class_name="ui-text"),
        rx.cond(
            PedidoAdminEstado.puede_cambiar,
            rx.el.div(
                rx.foreach(PedidoAdminEstado.siguientes, _accion),
                class_name="ui-admin__actions",
            ),
            rx.el.p(
                "El pedido esta cerrado: no admite mas cambios de estado.",
                class_name="ui-text ui-text--muted ui-text--small",
            ),
        ),
        class_name="ui-stack",
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
        "Puede que se haya borrado o que el link este mal.",
        action=ButtonLink("Ver todos los pedidos", href="/admin/pedidos"),
    )


def _error() -> rx.Component:
    return rx.el.div(
        Alert(
            title="No pudimos cargar el pedido",
            description=PedidoAdminEstado.error,
            tone="error",
        ),
        Button(
            "Reintentar",
            variant="secondary",
            on_click=PedidoAdminEstado.reintentar,
        ),
        class_name="ui-stack",
    )


def _contenido() -> Any:
    return rx.cond(
        PedidoAdminEstado.cargando,
        _esqueletos(),
        rx.cond(
            PedidoAdminEstado.error != "",
            _error(),
            rx.cond(
                PedidoAdminEstado.no_encontrado,
                _no_encontrado(),
                rx.el.div(_datos(), _lineas(), _acciones(), class_name="ui-stack"),
            ),
        ),
    )


@rx.page(
    route="/admin/pedidos/[pedido_id]",
    title="Pedido",
    on_load=PedidoAdminEstado.on_load,
)
def pedido_admin_pagina() -> rx.Component:
    return AppShell(
        Container(
            _volver(),
            PageHeader(PedidoAdminEstado.titulo),
            AdminTabs(active="pedidos"),
            _contenido(),
            class_name="ui-stack",
        ),
        nav=nav_de_cuenta(cart=False),
    )
