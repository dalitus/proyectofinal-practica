"""Pagina de inicio provisoria.

Mientras el catalogo se reconstruye sobre el esquema nuevo (Fase 6), la raiz
solo presenta la tienda y las dos entradas de sesion. Usa los tokens de
``app/ui/tokens.py`` y no declara colores ni sombras propias (T-063).
"""

import reflex as rx

from app.ui.tokens import COLORS, FONT, RADIUS, SPACE


def _boton(texto: str, ruta: str, primario: bool) -> rx.Component:
    fondo = COLORS["accent"] if primario else COLORS["card"]
    color = COLORS["accent_text"] if primario else COLORS["text"]
    return rx.button(
        texto,
        on_click=rx.redirect(ruta),
        background_color=fondo,
        color=color,
        border=f"1px solid {COLORS['border']}",
        border_radius=RADIUS["control"],
        padding=f"{SPACE['sm']} {SPACE['lg']}",
        font_family=FONT,
        font_weight="600",
        cursor="pointer",
    )


@rx.page(route="/", title="Tienda")
def inicio_pagina() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.heading(
                "Indumentaria y calzado",
                size="7",
                color=COLORS["text"],
                font_family=FONT,
            ),
            rx.text(
                "Estamos reconstruyendo el catalogo sobre el esquema nuevo. "
                "Mientras tanto, podes crear tu cuenta o iniciar sesion.",
                color=COLORS["muted"],
                font_family=FONT,
                text_align="center",
            ),
            rx.hstack(
                _boton("Iniciar sesion", "/login", primario=True),
                _boton("Crear cuenta", "/register", primario=False),
                spacing="3",
                justify="center",
                wrap="wrap",
            ),
            spacing="4",
            align="center",
            max_width="520px",
            padding=SPACE["xl"],
            background_color=COLORS["card"],
            border=f"1px solid {COLORS['border']}",
            border_radius=RADIUS["card"],
        ),
        min_height="100vh",
        background_color=COLORS["page"],
        padding=SPACE["md"],
    )
