"""Consultas del comprador en ``/consultas`` (T-065, D-002, D-030).

El comprador escribe su consulta y lee la respuesta en la web: no hay correo
(D-030). La pagina solo compone; el autor sale del token en el estado y la lista
trae unicamente sus filas.
"""

from __future__ import annotations

from typing import Any

import reflex as rx

from app.pages.cuenta_menu import nav_de_cuenta
from app.state.mis_consultas_estado import MisConsultasEstado
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
    Skeleton,
)

ESQUELETOS_AL_CARGAR = 3


def _estado(consulta: Any) -> rx.Component:
    return rx.match(
        consulta["estado"],
        ("respondida", Badge(consulta["estado_etiqueta"], tone="success", quiet=True)),
        ("pendiente", Badge(consulta["estado_etiqueta"], tone="info", quiet=True)),
        Badge(consulta["estado_etiqueta"], tone="neutral", quiet=True),
    )


def _respuesta(consulta: Any) -> rx.Component:
    """The answer is only rendered when it exists; the admin name may be empty."""
    return rx.cond(
        consulta["respuesta"] != "",
        rx.el.div(
            rx.el.h3("Respuesta", class_name="ui-text"),
            rx.el.p(consulta["respuesta"], class_name="ui-admin__message"),
            rx.el.p(
                "Respondio "
                + consulta["respondida_por"].to_string(use_json=False)
                + " el "
                + consulta["fecha_respuesta"].to_string(use_json=False)
                + ".",
                class_name="ui-text ui-text--muted ui-text--small",
            ),
            class_name="ui-stack",
        ),
        rx.el.p(
            "Todavia no tiene respuesta.",
            class_name="ui-text ui-text--muted ui-text--small",
        ),
    )


def _consulta(consulta: Any) -> rx.Component:
    return Card(
        rx.el.div(
            rx.el.div(
                rx.el.h2(consulta["asunto"], class_name="ui-text"),
                rx.el.span(
                    "Enviada el " + consulta["fecha"].to_string(use_json=False),
                    class_name="ui-text ui-text--muted ui-text--small",
                ),
                class_name="ui-stack",
            ),
            _estado(consulta),
            class_name="ui-admin__data",
        ),
        rx.el.p(consulta["mensaje"], class_name="ui-admin__message"),
        _respuesta(consulta),
        class_name="ui-stack",
    )


def _formulario() -> rx.Component:
    return Card(
        rx.el.h2("Nueva consulta", class_name="ui-text"),
        rx.el.p(
            "Contanos que necesitas y te respondemos en esta pagina.",
            class_name="ui-text ui-text--muted ui-text--small",
        ),
        rx.form(
            Input(
                label="Asunto",
                name="asunto",
                value=MisConsultasEstado.asunto,
                on_change=MisConsultasEstado.escribir_asunto,
                error=MisConsultasEstado.error_asunto,
                placeholder="Talle, envio, stock...",
                required=True,
                input_id="consulta-asunto",
                max_length=MisConsultasEstado.ASUNTO_MAXIMO,
            ),
            rx.el.div(
                rx.el.label(
                    "Consulta",
                    **{"html_for": "consulta-mensaje"},
                    class_name="ui-field__label",
                ),
                rx.el.textarea(
                    id="consulta-mensaje",
                    name="mensaje",
                    value=MisConsultasEstado.mensaje,
                    on_change=MisConsultasEstado.escribir_mensaje,
                    rows="6",
                    max_length=MisConsultasEstado.MENSAJE_MAXIMO,
                    required=True,
                    class_name="ui-input ui-textarea",
                    **{"aria-invalid": MisConsultasEstado.error_mensaje != ""},
                ),
                rx.cond(
                    MisConsultasEstado.error_mensaje != "",
                    rx.el.span(
                        MisConsultasEstado.error_mensaje,
                        class_name="ui-field__error",
                        role="alert",
                    ),
                    rx.fragment(),
                ),
                class_name="ui-field",
            ),
            rx.el.div(
                Button(
                    "Enviar consulta",
                    type="submit",
                    loading=MisConsultasEstado.enviando,
                ),
                rx.el.span(
                    "La respuesta se muestra aca, no se envia por correo.",
                    class_name="ui-text ui-text--muted ui-text--small",
                ),
                class_name="ui-admin__actions",
            ),
            on_submit=MisConsultasEstado.enviar,
            class_name="ui-stack",
        ),
        class_name="ui-stack",
    )


def _paginacion() -> rx.Component:
    return rx.cond(
        MisConsultasEstado.total_paginas > 1,
        rx.el.div(
            Button(
                "Anterior",
                variant="secondary",
                on_click=MisConsultasEstado.anterior,
                disabled=MisConsultasEstado.pagina <= 1,
            ),
            rx.el.span(
                "Pagina "
                + MisConsultasEstado.pagina.to_string()
                + " de "
                + MisConsultasEstado.total_paginas.to_string(),
                class_name="ui-pagination__info",
            ),
            Button(
                "Siguiente",
                variant="secondary",
                on_click=MisConsultasEstado.siguiente,
                disabled=MisConsultasEstado.pagina
                >= MisConsultasEstado.total_paginas,
            ),
            class_name="ui-pagination",
        ),
        rx.fragment(),
    )


def _esqueletos() -> rx.Component:
    return rx.el.div(
        *[Skeleton("block", height="220px") for _ in range(ESQUELETOS_AL_CARGAR)],
        class_name="ui-stack",
        **{"aria-hidden": "true"},
    )


def _vacio() -> rx.Component:
    return EmptyState(
        "Todavia no hiciste consultas",
        "Escribi la primera arriba y te respondemos en esta pagina.",
    )


def _error() -> rx.Component:
    return rx.el.div(
        Alert(
            title="No pudimos cargar tus consultas",
            description=MisConsultasEstado.error,
            tone="error",
        ),
        Button(
            "Reintentar",
            variant="secondary",
            on_click=MisConsultasEstado.reintentar,
        ),
        class_name="ui-stack",
    )


def _contenido() -> Any:
    return rx.cond(
        MisConsultasEstado.cargando,
        _esqueletos(),
        rx.cond(
            MisConsultasEstado.error != "",
            _error(),
            rx.cond(
                MisConsultasEstado.vacio,
                _vacio(),
                rx.el.div(
                    rx.foreach(MisConsultasEstado.consultas, _consulta),
                    _paginacion(),
                    class_name="ui-stack",
                ),
            ),
        ),
    )


@rx.page(
    route="/consultas",
    title="Mis consultas",
    on_load=MisConsultasEstado.on_load,
)
def mis_consultas_pagina() -> rx.Component:
    return AppShell(
        Container(
            PageHeader("Consultas", MisConsultasEstado.resumen),
            _formulario(),
            _contenido(),
            class_name="ui-stack",
        ),
        nav=nav_de_cuenta(),
    )
