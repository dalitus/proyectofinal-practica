"""Sin permiso en ``/403`` (T-023, D-021).

Un comprador autenticado que abre una ruta de admin cae aca; el invitado va al
login con retorno. La pagina no explica que existe del otro lado: solo dice que
su cuenta no tiene acceso.
"""

from __future__ import annotations

import reflex as rx

from app.pages.cuenta_menu import nav_de_cuenta
from app.ui import AppShell, ButtonLink, Container, EmptyState, PageHeader


@rx.page(route="/403", title="Sin permiso")
def no_autorizado_pagina() -> rx.Component:
    return AppShell(
        Container(
            PageHeader("Sin permiso"),
            EmptyState(
                "Tu cuenta no tiene acceso a esta seccion",
                "Si crees que es un error, escribinos y lo revisamos.",
                action=ButtonLink("Volver al catalogo", href="/"),
            ),
            class_name="ui-stack",
        ),
        nav=nav_de_cuenta(),
    )
