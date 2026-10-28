"""Pagina de alta de comprador.

Reemplaza la pagina ``/register`` del plugin: el alta tiene que crear
``LocalUser`` + ``UserProfile`` en una sola transaccion (T-022), y la del plugin
solo crea la credencial.

Solo maquetacion: los colores y espacios salen de ``app/ui/tokens.py`` y la
regla de negocio vive en ``app/service/auth_servicio.py``.
"""

import reflex as rx

from app.state.registro_estado import RegistroState
from app.ui.tokens import COLORS, FONT, RADIUS, SPACE

_FIELD_STYLE = {
    "background_color": COLORS["card"],
    "color": COLORS["text"],
    "border": f"1px solid {COLORS['border']}",
    "border_radius": RADIUS["control"],
    "font_family": FONT,
    "width": "100%",
}


def _campo(etiqueta: str, componente: rx.Component) -> rx.Component:
    return rx.vstack(
        rx.text(
            etiqueta,
            color=COLORS["muted"],
            font_family=FONT,
            font_size="0.875rem",
            font_weight="500",
        ),
        componente,
        spacing="1",
        align="start",
        width="100%",
    )


def _mensaje_error() -> rx.Component:
    return rx.cond(
        RegistroState.error != "",
        rx.text(
            RegistroState.error,
            color=COLORS["danger"],
            font_family=FONT,
            font_size="0.875rem",
            role="alert",
        ),
    )


@rx.page(route="/register", title="Crear cuenta")
def registro_pagina() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.heading(
                "Crear cuenta",
                size="6",
                color=COLORS["text"],
                font_family=FONT,
            ),
            rx.text(
                "Con tu cuenta podes comprar y seguir tus pedidos.",
                color=COLORS["muted"],
                font_family=FONT,
                font_size="0.875rem",
            ),
            _mensaje_error(),
            _campo(
                "Nombre",
                rx.input(
                    value=RegistroState.nombre,
                    on_change=RegistroState.set_nombre,
                    placeholder="Como queres que te llamemos",
                    style=_FIELD_STYLE,
                ),
            ),
            _campo(
                "Email",
                rx.input(
                    value=RegistroState.email,
                    on_change=RegistroState.set_email,
                    type="email",
                    placeholder="tu@email.com",
                    style=_FIELD_STYLE,
                ),
            ),
            _campo(
                "Contrasena",
                rx.input(
                    value=RegistroState.password,
                    on_change=RegistroState.set_password,
                    type="password",
                    placeholder="Al menos 8 caracteres",
                    style=_FIELD_STYLE,
                ),
            ),
            _campo(
                "Repetir contrasena",
                rx.input(
                    value=RegistroState.confirmacion,
                    on_change=RegistroState.set_confirmacion,
                    type="password",
                    placeholder="La misma contrasena",
                    style=_FIELD_STYLE,
                ),
            ),
            rx.button(
                rx.cond(RegistroState.enviando, "Creando cuenta...", "Crear cuenta"),
                on_click=RegistroState.enviar,
                disabled=RegistroState.enviando,
                background_color=COLORS["accent"],
                color=COLORS["accent_text"],
                border_radius=RADIUS["control"],
                padding=f"{SPACE['sm']} {SPACE['lg']}",
                font_family=FONT,
                font_weight="600",
                width="100%",
                cursor="pointer",
            ),
            rx.link(
                "Ya tengo cuenta",
                href="/login",
                color=COLORS["muted"],
                font_family=FONT,
                font_size="0.875rem",
            ),
            spacing="3",
            align="start",
            width="100%",
            max_width="380px",
            padding=SPACE["xl"],
            background_color=COLORS["card"],
            border=f"1px solid {COLORS['border']}",
            border_radius=RADIUS["card"],
        ),
        min_height="100vh",
        background_color=COLORS["page"],
        padding=SPACE["md"],
    )
