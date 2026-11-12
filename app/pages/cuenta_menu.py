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
from app.ui import TopNav, TopNavLink


def _boton_salir() -> rx.Component:
    """Logout is a button, not a link, so it owns its markup (T-078)."""
    return rx.el.button(
        rx.icon("log-out", size=16, **{"aria-hidden": "true"}),
        rx.el.span("Salir", class_name="ui-topnav__label"),
        on_click=SesionEstado.cerrar_sesion,
        type="button",
        class_name="ui-topnav__link ui-topnav__link--button",
        **{"aria-label": "Salir"},
    )


def MenuDeCuenta() -> rx.Component:
    """Session-aware account area for ``TopNav(account=...)``."""
    return rx.cond(
        SesionEstado.cuenta["logueado"],
        rx.el.div(
            rx.cond(
                SesionEstado.cuenta["es_admin"],
                TopNavLink("Panel", href="/admin/pedidos", icon="layout-dashboard"),
                rx.el.div(
                    TopNavLink("Mis pedidos", href="/pedidos", icon="package"),
                    TopNavLink("Mis consultas", href="/consultas", icon="message-square"),
                    class_name="ui-topnav__account",
                ),
            ),
            rx.el.span(
                SesionEstado.cuenta["nombre"],
                class_name="ui-topnav__link ui-topnav__link--muted",
            ),
            _boton_salir(),
            class_name="ui-topnav__account",
        ),
        rx.el.div(
            TopNavLink("Iniciar sesión", href="/login", icon="log-in"),
            TopNavLink("Crear cuenta", href="/register", icon="user-plus"),
            class_name="ui-topnav__account",
        ),
    )


def nav_de_cuenta(*, cart: bool = True) -> rx.Component:
    """Header for every page; the admin panel hides the cart (T-023, D-050).

    On buyer pages the cart link is hidden for the admin once the role resolves,
    even though the add-to-cart action is rejected server-side anyway. The badge
    count is a cached var of ``SesionEstado`` (T-078): the UI layer stays unaware
    of states, it only receives the number.
    """
    return TopNav(
        account=MenuDeCuenta(),
        cart=~SesionEstado.cuenta["es_admin"] if cart else False,
        cart_count=SesionEstado.unidades_carrito if cart else 0,
    )
