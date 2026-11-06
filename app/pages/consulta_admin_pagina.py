"""Detalle y respuesta de una consulta en ``/admin/consultas/[consulta_id]`` (T-052).

El mensaje se lee completo y la respuesta se escribe aca mismo; una consulta ya
respondida no se puede sobrescribir (el servicio lo rechaza aunque el formulario
aparezca). El borrado pide confirmacion y queda auditado (T-053).
"""

from __future__ import annotations

from typing import Any

import reflex as rx

from app.pages.cuenta_menu import nav_de_cuenta
from app.state.consultas_admin_estado import ConsultaAdminEstado
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
    return rx.el.a("Volver a consultas", href="/admin/consultas", class_name="ui-back")


def _estado() -> rx.Component:
    return rx.match(
        ConsultaAdminEstado.consulta["estado"],
        (
            "respondida",
            Badge(ConsultaAdminEstado.consulta["estado_etiqueta"], tone="success", quiet=True),
        ),
        (
            "pendiente",
            Badge(ConsultaAdminEstado.consulta["estado_etiqueta"], tone="info", quiet=True),
        ),
        Badge(ConsultaAdminEstado.consulta["estado_etiqueta"], tone="neutral", quiet=True),
    )


def _mensaje() -> rx.Component:
    return Card(
        rx.el.div(
            rx.el.div(
                rx.el.span("De", class_name="ui-text ui-text--muted ui-text--small"),
                rx.el.span(ConsultaAdminEstado.consulta["cliente"], class_name="ui-table__strong"),
                rx.el.span(ConsultaAdminEstado.consulta["email"], class_name="ui-table__muted"),
                class_name="ui-admin__field",
            ),
            rx.el.div(
                rx.el.span("Fecha", class_name="ui-text ui-text--muted ui-text--small"),
                rx.el.span(ConsultaAdminEstado.consulta["fecha"]),
                class_name="ui-admin__field",
            ),
            rx.el.div(
                rx.el.span("Estado", class_name="ui-text ui-text--muted ui-text--small"),
                _estado(),
                class_name="ui-admin__field",
            ),
            class_name="ui-admin__data",
        ),
        rx.el.h2(
            ConsultaAdminEstado.consulta["asunto"],
            class_name="ui-text",
        ),
        rx.el.p(
            ConsultaAdminEstado.consulta["mensaje"],
            class_name="ui-admin__message",
        ),
        class_name="ui-stack",
    )


def _respuesta_existente() -> rx.Component:
    return Card(
        rx.el.h2("Respuesta", class_name="ui-text"),
        rx.el.p(
            ConsultaAdminEstado.consulta["respuesta"],
            class_name="ui-admin__message",
        ),
        rx.el.p(
            "Respondio "
            + ConsultaAdminEstado.consulta["respondida_por"].to_string(use_json=False)
            + " el "
            + ConsultaAdminEstado.consulta["fecha_respuesta"].to_string(use_json=False)
            + ".",
            class_name="ui-text ui-text--muted ui-text--small",
        ),
        class_name="ui-stack",
    )


def _formulario() -> rx.Component:
    return Card(
        rx.el.h2("Responder", class_name="ui-text"),
        rx.form(
            rx.el.div(
                rx.el.label(
                    "Respuesta",
                    **{"html_for": "admin-consulta-respuesta"},
                    class_name="ui-field__label",
                ),
                rx.el.textarea(
                    id="admin-consulta-respuesta",
                    name="respuesta",
                    value=ConsultaAdminEstado.borrador,
                    on_change=ConsultaAdminEstado.escribir,
                    rows="6",
                    max_length=ConsultaAdminEstado.MAXIMO,
                    class_name="ui-input ui-textarea",
                    **{"aria-invalid": ConsultaAdminEstado.error_borrador != ""},
                ),
                rx.cond(
                    ConsultaAdminEstado.error_borrador != "",
                    rx.el.span(
                        ConsultaAdminEstado.error_borrador,
                        class_name="ui-field__error",
                        role="alert",
                    ),
                    rx.fragment(),
                ),
                class_name="ui-field",
            ),
            rx.el.div(
                Button(
                    "Responder",
                    type="submit",
                    loading=ConsultaAdminEstado.enviando,
                ),
                rx.el.span(
                    "La respuesta se muestra en la web, no se envia por correo.",
                    class_name="ui-text ui-text--muted ui-text--small",
                ),
                class_name="ui-admin__actions",
            ),
            on_submit=ConsultaAdminEstado.responder,
            class_name="ui-stack",
        ),
        class_name="ui-stack",
    )


def _borrar() -> rx.Component:
    return Card(
        rx.el.h2("Eliminar la consulta", class_name="ui-text"),
        rx.el.p(
            "Se borra el mensaje y su respuesta. Esta accion no se puede deshacer.",
            class_name="ui-text ui-text--muted ui-text--small",
        ),
        ConfirmDialog(
            trigger=Button("Eliminar consulta", variant="danger"),
            title="Eliminar la consulta",
            description=("Se borra el mensaje y su respuesta. Esta accion no se puede deshacer."),
            confirm_label="Eliminar",
            cancel_label="Volver",
            on_confirm=ConsultaAdminEstado.eliminar,
        ),
        class_name="ui-stack",
    )


def _esqueletos() -> rx.Component:
    return rx.el.div(
        Skeleton("block", height="220px"),
        Skeleton("block", height="160px"),
        class_name="ui-stack",
        **{"aria-hidden": "true"},
    )


def _no_encontrada() -> rx.Component:
    return EmptyState(
        "Esa consulta no existe",
        "Puede que se haya borrado o que el link este mal.",
        action=ButtonLink("Ver todas las consultas", href="/admin/consultas"),
    )


def _error() -> rx.Component:
    return rx.el.div(
        Alert(
            title="No pudimos cargar la consulta",
            description=ConsultaAdminEstado.error,
            tone="error",
        ),
        Button(
            "Reintentar",
            variant="secondary",
            on_click=ConsultaAdminEstado.reintentar,
        ),
        class_name="ui-stack",
    )


def _contenido() -> Any:
    return rx.cond(
        ConsultaAdminEstado.cargando,
        _esqueletos(),
        rx.cond(
            ConsultaAdminEstado.error != "",
            _error(),
            rx.cond(
                ConsultaAdminEstado.no_encontrada,
                _no_encontrada(),
                rx.el.div(
                    _mensaje(),
                    rx.cond(
                        ConsultaAdminEstado.pendiente,
                        _formulario(),
                        _respuesta_existente(),
                    ),
                    _borrar(),
                    class_name="ui-stack",
                ),
            ),
        ),
    )


@rx.page(
    route="/admin/consultas/[consulta_id]",
    title="Consulta",
    on_load=ConsultaAdminEstado.on_load,
)
def consulta_admin_pagina() -> rx.Component:
    return AppShell(
        Container(
            _volver(),
            PageHeader(ConsultaAdminEstado.titulo),
            AdminTabs(active="consultas"),
            _contenido(),
            class_name="ui-stack",
        ),
        nav=nav_de_cuenta(cart=False),
    )
