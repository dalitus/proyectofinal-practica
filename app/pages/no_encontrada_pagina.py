"""Ruta inexistente con salida clara (T-061, D-024).

Reflex reserva ``/404`` para la pagina que se muestra cuando ninguna ruta
coincide. Sin esto el framework pinta su texto en ingles; con esto el visitante
ve el mismo shell del sitio y un camino de vuelta al catalogo.
"""

from __future__ import annotations

import reflex as rx

from app.pages.cuenta_menu import nav_de_cuenta
from app.ui import AppShell, ButtonLink, Container, EmptyState


@rx.page(route="/404", title="Pagina no encontrada")
def no_encontrada_pagina() -> rx.Component:
    return AppShell(
        Container(
            EmptyState(
                "No encontramos esa pagina",
                "Puede que el link este mal o que la pagina ya no exista.",
                action=ButtonLink("Volver al catalogo", href="/"),
            ),
            class_name="ui-stack",
        ),
        nav=nav_de_cuenta(),
    )
