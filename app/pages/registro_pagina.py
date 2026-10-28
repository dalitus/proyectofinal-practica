"""Comprador sign-up page.

Replaces the plugin ``/register`` page: the sign-up has to create ``LocalUser`` +
``UserProfile`` in one transaction (T-022), and the plugin page only creates the
credential.

Layout only: the visuals come from ``app/ui`` and the business rule lives in
``app/service/auth_servicio.py``.
"""

import reflex as rx

from app.state.registro_estado import RegistroState
from app.ui import Alert, AppShell, Button, Card, Container, Input, PageHeader


@rx.page(route="/register", title="Crear cuenta")
def registro_pagina() -> rx.Component:
    return AppShell(
        Container(
            rx.el.div(
                PageHeader(
                    "Crear cuenta",
                    "Con tu cuenta podes comprar y seguir tus pedidos.",
                ),
                Card(
                    rx.cond(
                        RegistroState.error != "",
                        Alert(
                            title="No pudimos crear la cuenta",
                            description=RegistroState.error,
                            tone="error",
                        ),
                        rx.fragment(),
                    ),
                    Input(
                        label="Nombre",
                        value=RegistroState.nombre,
                        on_change=RegistroState.set_nombre,
                        placeholder="Como queres que te llamemos",
                        required=True,
                    ),
                    Input(
                        label="Email",
                        value=RegistroState.email,
                        on_change=RegistroState.set_email,
                        type="email",
                        placeholder="tu@email.com",
                        required=True,
                    ),
                    Input(
                        label="Contrasena",
                        value=RegistroState.password,
                        on_change=RegistroState.set_password,
                        type="password",
                        placeholder="Al menos 8 caracteres",
                        required=True,
                    ),
                    Input(
                        label="Repetir contrasena",
                        value=RegistroState.confirmacion,
                        on_change=RegistroState.set_confirmacion,
                        type="password",
                        placeholder="La misma contrasena",
                        required=True,
                    ),
                    Button(
                        "Crear cuenta",
                        loading=RegistroState.enviando,
                        on_click=RegistroState.enviar,
                        width="100%",
                    ),
                    rx.el.a(
                        "Ya tengo cuenta",
                        href="/login",
                        class_name="ui-topnav__link",
                    ),
                    class_name="ui-stack",
                ),
                class_name="ui-column",
            ),
        )
    )
