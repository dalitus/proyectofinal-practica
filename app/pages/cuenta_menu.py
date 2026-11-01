"""Menu de cuenta del header (T-021).

El header es el mismo en todas las paginas, pero ``app/ui`` no conoce estados
(design.md 3): este modulo arma el pedazo que si sabe quien esta conectado y las
paginas lo pasan como slot de ``AppShell``.

Con sesion muestra el nombre, el acceso al panel si el rol es admin y "Salir";
sin sesion, las dos entradas de siempre. El rol se lee de ``SesionEstado``, que
lo resuelve contra la base: esconder el link no es el permiso (D-021), las rutas
del panel tienen su propia guarda.
"""

from __future__ import annotations

import reflex as rx

from app.state.sesion_estado import SesionEstado
from app.ui import TopNav


def MenuDeCuenta() -> rx.Component:
    """Session-aware account area for ``TopNav(account=...)``."""
    return rx.cond(
        SesionEstado.cuenta["logueado"],
        rx.el.div(
            rx.cond(
                SesionEstado.cuenta["es_admin"],
                rx.el.a("Panel", href="/admin/pedidos", class_name="ui-topnav__link"),
                rx.fragment(),
            ),
            rx.el.span(
                SesionEstado.cuenta["nombre"],
                class_name="ui-topnav__link ui-topnav__link--muted",
            ),
            rx.el.button(
                "Salir",
                on_click=SesionEstado.cerrar_sesion,
                type="button",
                class_name="ui-topnav__link ui-topnav__link--button",
            ),
            class_name="ui-topnav__account",
        ),
        rx.el.div(
            rx.el.a("Iniciar sesión", href="/login", class_name="ui-topnav__link"),
            rx.el.a("Crear cuenta", href="/register", class_name="ui-topnav__link"),
            class_name="ui-topnav__account",
        ),
    )


def nav_de_cuenta(*, cart: bool = True) -> rx.Component:
    """Header for every page; ``cart=False`` in the admin panel (T-023)."""
    return TopNav(account=MenuDeCuenta(), cart=cart)
