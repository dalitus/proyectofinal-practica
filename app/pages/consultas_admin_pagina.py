"""Consultas del admin en ``/admin/consultas`` (T-052, D-030).

Una tabla con filtro y paginacion; la respuesta se escribe en el detalle. No hay
envio por correo ni archivado: el comprador lee la respuesta en la web (D-030).
"""

from __future__ import annotations

from typing import Any

import reflex as rx

from app.pages.cuenta_menu import nav_de_cuenta
from app.state.consultas_admin_estado import ConsultasAdminEstado
from app.ui import (
    AdminTabs,
    Alert,
    AppShell,
    Badge,
    Button,
    ButtonLink,
    Container,
    EmptyState,
    PageHeader,
    Select,
    Skeleton,
)

ESQUELETOS_AL_CARGAR = 5


def _estado(consulta: Any) -> rx.Component:
    return rx.match(
        consulta["estado"],
        ("respondida", Badge(consulta["estado_etiqueta"], tone="success", quiet=True)),
        ("pendiente", Badge(consulta["estado_etiqueta"], tone="info", quiet=True)),
        Badge(consulta["estado_etiqueta"], tone="neutral", quiet=True),
    )


def _fila(consulta: Any) -> rx.Component:
    return rx.el.tr(
        rx.el.td("#" + consulta["id"].to_string()),
        rx.el.td(
            rx.el.span(consulta["asunto"], class_name="ui-table__strong"),
            rx.el.span(consulta["resumen"], class_name="ui-table__muted"),
            class_name="ui-table__stack",
        ),
        rx.el.td(
            rx.el.span(consulta["cliente"], class_name="ui-table__strong"),
            rx.el.span(consulta["email"], class_name="ui-table__muted"),
            class_name="ui-table__stack",
        ),
        rx.el.td(consulta["fecha"]),
        rx.el.td(_estado(consulta)),
        rx.el.td(
            rx.cond(
                consulta["respondida_por"] != "",
                consulta["respondida_por"],
                rx.el.span("-", class_name="ui-table__muted"),
            )
        ),
        rx.el.td(
            ButtonLink(
                "Ver",
                href="/admin/consultas/" + consulta["id"].to_string(),
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
                    rx.el.th("Consulta"),
                    rx.el.th("Cliente"),
                    rx.el.th("Fecha"),
                    rx.el.th("Estado"),
                    rx.el.th("Respondio"),
                    rx.el.th("", class_name="ui-table__actions"),
                )
            ),
            rx.el.tbody(rx.foreach(ConsultasAdminEstado.consultas, _fila)),
            class_name="ui-table",
        ),
        class_name="ui-table-wrap",
    )


def _esqueletos() -> rx.Component:
    return rx.el.div(
        Skeleton("block", height="260px"),
        class_name="ui-table-wrap",
        **{"aria-hidden": "true"},
    )


def _filtros() -> rx.Component:
    return rx.el.div(
        Select(
            opciones=ConsultasAdminEstado.filtros,
            label="Estado",
            value=ConsultasAdminEstado.filtro,
            on_change=ConsultasAdminEstado.filtrar,
            input_id="admin-consultas-estado",
        ),
        class_name="ui-admin__filters",
    )


def _paginacion() -> rx.Component:
    return rx.el.div(
        Button(
            "Anterior",
            variant="secondary",
            on_click=ConsultasAdminEstado.anterior,
            disabled=ConsultasAdminEstado.pagina <= 1,
        ),
        rx.el.span(
            "Pagina "
            + ConsultasAdminEstado.pagina.to_string()
            + " de "
            + ConsultasAdminEstado.total_paginas.to_string(),
            class_name="ui-pagination__info",
        ),
        Button(
            "Siguiente",
            variant="secondary",
            on_click=ConsultasAdminEstado.siguiente,
            disabled=ConsultasAdminEstado.pagina >= ConsultasAdminEstado.total_paginas,
        ),
        class_name="ui-pagination",
    )


def _vacio() -> rx.Component:
    return EmptyState(
        "No hay consultas con este filtro",
        "Proba con otro estado.",
        action=Button(
            "Ver todas",
            variant="secondary",
            on_click=ConsultasAdminEstado.filtrar(""),
        ),
    )


def _error() -> rx.Component:
    return rx.el.div(
        Alert(
            title="No pudimos cargar las consultas",
            description=ConsultasAdminEstado.error,
            tone="error",
        ),
        Button(
            "Reintentar",
            variant="secondary",
            on_click=ConsultasAdminEstado.reintentar,
        ),
        class_name="ui-stack",
    )


def _contenido() -> Any:
    return rx.cond(
        ConsultasAdminEstado.cargando,
        _esqueletos(),
        rx.cond(
            ConsultasAdminEstado.error != "",
            _error(),
            rx.cond(
                ConsultasAdminEstado.vacio,
                _vacio(),
                rx.el.div(_tabla(), _paginacion(), class_name="ui-stack"),
            ),
        ),
    )


@rx.page(
    route="/admin/consultas",
    title="Consultas",
    on_load=ConsultasAdminEstado.on_load,
)
def consultas_admin_pagina() -> rx.Component:
    return AppShell(
        Container(
            PageHeader("Consultas", ConsultasAdminEstado.resumen),
            AdminTabs(active="consultas"),
            _filtros(),
            _contenido(),
            class_name="ui-stack",
        ),
        nav=nav_de_cuenta(cart=False),
    )
