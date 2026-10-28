"""Provisional landing page.

While the catalog is rebuilt on the new schema (Fase 6), the root only presents
the shop and the two session entry points. Layout and primitives come from
``app/ui``; this module declares no colour, spacing or shadow of its own (T-063).
"""

import reflex as rx

from app.ui import AppShell, Button, Card, Container, PageHeader


@rx.page(route="/", title="Tienda")
def inicio_pagina() -> rx.Component:
    return AppShell(
        Container(
            PageHeader(
                "Indumentaria y calzado",
                "Estamos reconstruyendo el catalogo sobre el esquema nuevo.",
            ),
            Card(
                rx.el.p(
                    "Mientras tanto, podes crear tu cuenta o iniciar sesion.",
                    class_name="ui-text ui-text--muted",
                ),
                rx.el.div(
                    Button("Iniciar sesion", on_click=rx.redirect("/login")),
                    Button(
                        "Crear cuenta",
                        variant="secondary",
                        on_click=rx.redirect("/register"),
                    ),
                    class_name="ui-row",
                ),
                class_name="ui-stack",
            ),
        )
    )
