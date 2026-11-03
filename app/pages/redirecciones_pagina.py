"""Rutas viejas que redirigen a la URL canonica (T-061, D-024).

El sitio cambio de URLs varias veces y hay links guardados por ahi. En vez de
mantener dos implementaciones por pantalla, cada ruta vieja redirige a la nueva:
``/catalogo`` -> ``/``, ``/users`` y ``/user`` -> ``/login``, y
``/detalle_producto`` -> ``/`` porque el detalle canonico necesita un id en la
URL y la pantalla vieja lo leia del estado.

No se registra ninguna dos veces: ``app/app.py`` solo importa estos modulos.
"""

from __future__ import annotations

import reflex as rx

from app.pages.cuenta_menu import nav_de_cuenta
from app.ui import AppShell, Container, Skeleton


def _redirigiendo() -> rx.Component:
    """Skeleton instead of a spinner: the redirect lasts one round trip."""
    return AppShell(
        Container(
            Skeleton("block", height="240px"),
            class_name="ui-stack",
            **{"aria-hidden": "true"},
        ),
        nav=nav_de_cuenta(),
    )


@rx.page(route="/catalogo", on_load=rx.redirect("/", replace=True))
def redireccion_catalogo() -> rx.Component:
    return _redirigiendo()


@rx.page(route="/users", on_load=rx.redirect("/login", replace=True))
def redireccion_users() -> rx.Component:
    return _redirigiendo()


@rx.page(route="/user", on_load=rx.redirect("/login", replace=True))
def redireccion_user() -> rx.Component:
    return _redirigiendo()


@rx.page(route="/detalle_producto", on_load=rx.redirect("/", replace=True))
def redireccion_detalle() -> rx.Component:
    return _redirigiendo()
