"""Application shell: AppShell, TopNav, Container, PageHeader, Footer.

Pages return ``AppShell(...)`` and stop repeating the canvas colour, the
min-height and the 1200px container (docs/design.md 3). The shell is a slot-based
API: auth-aware pieces (account menu, cart count, search binding) are passed in by
the page that owns the state, so ``app/ui`` never imports a Reflex state.
"""

from __future__ import annotations

from typing import Any

import reflex as rx

DEFAULT_BRAND = "Calzado Fermin 👠"
DEFAULT_FOOTER = "Calzado Fermin"


def _join(*class_names: str | None) -> str:
    return " ".join(name for name in class_names if name)


def Container(*children: Any, class_name: str | None = None, **props: Any) -> rx.Component:
    """Centred column: max-width 1200px, 16px padding (24px from 768px up)."""
    return rx.el.div(*children, class_name=_join("ui-container", class_name), **props)


def TopNav(
    *,
    brand: str = DEFAULT_BRAND,
    brand_href: str = "/",
    search: rx.Component | None = None,
    account: rx.Component | None = None,
    links: list[rx.Component] | None = None,
    cart: bool = True,
    class_name: str | None = None,
) -> rx.Component:
    """Sticky header: brand, optional search, nav links, account area.

    ``account`` and ``search`` are slots. When ``account`` is omitted the header
    shows the guest entry points; a page with a session passes its own component
    instead of the shell guessing. ``cart=False`` is for the admin panel, where
    the buyer's cart is not part of the job (T-023).
    """
    inner: list[Any] = [
        rx.el.a(brand, href=brand_href, class_name="ui-topnav__brand"),
    ]

    if search is not None:
        inner.append(rx.el.div(search, class_name="ui-topnav__search"))

    if account is None:
        account = rx.fragment(
            rx.el.a("Iniciar sesión", href="/login", class_name="ui-topnav__link"),
            rx.el.a("Crear cuenta", href="/register", class_name="ui-topnav__link"),
        )

    inner.append(
        rx.el.nav(
            *(links or []),
            *(
                [rx.el.a("Carrito", href="/carrito", class_name="ui-topnav__link")]
                if cart
                else []
            ),
            account,
            class_name="ui-topnav__nav",
        )
    )

    return rx.el.header(
        rx.el.div(*inner, class_name="ui-topnav__inner"),
        class_name=_join("ui-topnav", class_name),
    )


# Secciones del panel que ya existen. Productos llega con T-050 y se agrega aca,
# no como un link muerto en la navegacion.
SECCIONES_DE_ADMIN = (
    ("pedidos", "Pedidos", "/admin/pedidos"),
    ("consultas", "Consultas", "/admin/consultas"),
)


def AdminTabs(*, active: str, class_name: str | None = None) -> rx.Component:
    """Admin section nav: the current tab is marked for sight and for screen readers."""
    enlaces: list[rx.Component] = []
    for clave, etiqueta, href in SECCIONES_DE_ADMIN:
        activo = clave == active
        enlaces.append(
            rx.el.a(
                etiqueta,
                href=href,
                class_name=_join(
                    "ui-admin__tab",
                    "ui-admin__tab--active" if activo else None,
                ),
                **({"aria-current": "page"} if activo else {}),
            )
        )

    return rx.el.nav(
        *enlaces,
        class_name=_join("ui-admin__tabs", class_name),
        **{"aria-label": "Secciones de administracion"},
    )


def PageHeader(
    title: Any,
    subtitle: Any = None,
    actions: rx.Component | None = None,
    *,
    class_name: str | None = None,
) -> rx.Component:
    """Page title, optional subtitle and optional action group."""
    text: list[Any] = [rx.el.h1(title, class_name="ui-page-header__title")]
    if subtitle is not None:
        text.append(rx.el.p(subtitle, class_name="ui-page-header__subtitle"))

    children: list[Any] = [rx.el.div(*text, class_name="ui-page-header__text")]
    if actions is not None:
        children.append(rx.el.div(actions, class_name="ui-page-header__actions"))

    return rx.el.div(*children, class_name=_join("ui-page-header", class_name))


def Footer(text: str = DEFAULT_FOOTER) -> rx.Component:
    """One muted line, separated by a 1px border."""
    return rx.el.footer(
        rx.el.div(text, class_name="ui-footer__inner"),
        class_name="ui-footer",
    )


def AppShell(
    *children: Any,
    nav: rx.Component | None = None,
    footer: bool = True,
    footer_text: str = DEFAULT_FOOTER,
    class_name: str | None = None,
) -> rx.Component:
    """Nav + main + footer over the ``page`` canvas."""
    if nav is None:
        nav = TopNav()

    inner: list[Any] = [
        nav,
        rx.el.main(*children, class_name="ui-main"),
    ]
    if footer:
        inner.append(Footer(footer_text))

    return rx.el.div(*inner, class_name=_join("ui-shell", class_name))
