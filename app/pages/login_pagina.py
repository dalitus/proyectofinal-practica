"""Iniciar sesión page.

Replaces the plugin ``/login`` page: that one is in English and its
``LoginState`` errors ("There was a problem logging in...") never reach a
Spanish UI. The credentials rule lives in ``app/service/auth_servicio.py`` and
the form state in ``app/state/login_estado.py`` (T-021).

Layout only: the visuals come from ``app/ui``.
"""

import reflex as rx

from app.pages.cuenta_menu import nav_de_cuenta
from app.state.login_estado import LoginEstado
from app.ui import Alert, AppShell, Button, Card, Container, Input, PageHeader


@rx.page(route="/login", title="Iniciar sesión", on_load=LoginEstado.on_load)
def login_pagina() -> rx.Component:
    return AppShell(
        Container(
            rx.el.div(
                PageHeader(
                    "Iniciar sesión",
                    "Entrá con tu cuenta para comprar y seguir tus pedidos.",
                ),
                Card(
                    rx.cond(
                        LoginEstado.error != "",
                        Alert(
                            title="No pudimos iniciar sesión",
                            description=LoginEstado.error,
                            tone="error",
                        ),
                        rx.fragment(),
                    ),
                    rx.form.root(
                        rx.el.div(
                            Input(
                                label="Email",
                                name="email",
                                type="email",
                                value=LoginEstado.email,
                                on_change=LoginEstado.set_email,
                                placeholder="tu@email.com",
                                required=True,
                            ),
                            Input(
                                label="Contraseña",
                                name="password",
                                type="password",
                                value=LoginEstado.password,
                                on_change=LoginEstado.set_password,
                                placeholder="Tu contraseña",
                                required=True,
                            ),
                            Button(
                                "Entrar",
                                type="submit",
                                loading=LoginEstado.enviando,
                                width="100%",
                            ),
                            class_name="ui-stack",
                        ),
                        on_submit=LoginEstado.enviar,
                        reset_on_submit=False,
                    ),
                    rx.el.a(
                        "¿No tenés cuenta? Creá una",
                        href="/register",
                        class_name="ui-topnav__link",
                    ),
                    class_name="ui-stack",
                ),
                class_name="ui-column",
            ),
        ),
        nav=nav_de_cuenta(),
    )
