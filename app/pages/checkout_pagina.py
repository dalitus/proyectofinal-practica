"""Checkout en ``/checkout`` (T-043, design.md 5).

Solo composicion: las lineas y el total llegan ya calculados y formateados del
servicio. Un unico CTA primario ("Confirmar pedido") y el formulario con error por
campo (design.md 4.3). No hay pago online: el pedido queda registrado y el envio
se coordina despues (D-005).
"""

from __future__ import annotations

from typing import Any

import reflex as rx

from app.pages.cuenta_menu import nav_de_cuenta
from app.state.checkout_estado import CheckoutEstado
from app.ui import (
    Alert,
    AppShell,
    Button,
    ButtonLink,
    Card,
    Container,
    Input,
    PageHeader,
    Skeleton,
)


def _campo(
    *,
    label: str,
    name: str,
    value: Any,
    on_change: Any,
    error: Any,
    type: str = "text",
    placeholder: str | None = None,
    wide: bool = False,
) -> rx.Component:
    """One labelled input with its inline error (design.md 4.3)."""
    return rx.el.div(
        Input(
            label=label,
            name=name,
            type=type,
            value=value,
            on_change=on_change,
            error=error,
            placeholder=placeholder,
        ),
        class_name="ui-checkout__wide" if wide else "",
    )


def _formulario() -> rx.Component:
    """AddressForm: error per field, never a single banner for everything."""
    return Card(
        rx.el.h2("Datos de entrega", class_name="ui-checkout__title"),
        rx.form.root(
            rx.el.div(
                _campo(
                    label="Direccion",
                    name="direccion",
                    value=CheckoutEstado.direccion,
                    on_change=CheckoutEstado.set_direccion,
                    error=CheckoutEstado.error_direccion,
                    placeholder="Calle o avenida",
                    wide=True,
                ),
                _campo(
                    label="Numero",
                    name="numero",
                    value=CheckoutEstado.numero,
                    on_change=CheckoutEstado.set_numero,
                    error=CheckoutEstado.error_numero,
                    placeholder="1234",
                ),
                _campo(
                    label="Departamento (opcional)",
                    name="departamento",
                    value=CheckoutEstado.departamento,
                    on_change=CheckoutEstado.set_departamento,
                    error="",
                    placeholder="Piso y depto",
                ),
                _campo(
                    label="Codigo postal (opcional)",
                    name="codigo_postal",
                    value=CheckoutEstado.codigo_postal,
                    on_change=CheckoutEstado.set_codigo_postal,
                    error="",
                    placeholder="1425",
                ),
                _campo(
                    label="Ciudad",
                    name="ciudad",
                    value=CheckoutEstado.ciudad,
                    on_change=CheckoutEstado.set_ciudad,
                    error=CheckoutEstado.error_ciudad,
                    placeholder="CABA",
                ),
                _campo(
                    label="Provincia",
                    name="provincia",
                    value=CheckoutEstado.provincia,
                    on_change=CheckoutEstado.set_provincia,
                    error=CheckoutEstado.error_provincia,
                    placeholder="Buenos Aires",
                ),
                class_name="ui-checkout__fields",
            ),
            Button(
                "Confirmar pedido",
                type="submit",
                loading=CheckoutEstado.enviando,
                width="100%",
            ),
            on_submit=CheckoutEstado.confirmar,
            reset_on_submit=False,
            class_name="ui-checkout__form",
        ),
        class_name="ui-checkout__card",
    )


def _items() -> rx.Component:
    """Compact list of what is being bought, so the total is not a surprise."""
    return rx.el.ul(
        rx.foreach(
            CheckoutEstado.lineas,
            lambda linea: rx.el.li(
                rx.el.span(
                    linea["nombre"].to_string(use_json=False)
                    + " ("
                    + linea["color"].to_string(use_json=False)
                    + ", "
                    + linea["talle"].to_string(use_json=False)
                    + ")",
                ),
                rx.el.span("x" + linea["cantidad"].to_string()),
                class_name="ui-checkout__item",
            ),
        ),
        class_name="ui-checkout__items",
    )


def _resumen() -> rx.Component:
    """OrderSummary: sticky from 1024px, one primary CTA (design.md 5)."""
    return rx.el.aside(
        rx.el.h2("Resumen", class_name="ui-cart__summary-title"),
        _items(),
        rx.el.div(
            rx.el.span("Subtotal"),
            rx.el.span(CheckoutEstado.subtotal),
            class_name="ui-cart__row",
        ),
        rx.el.div(
            rx.el.span("Envio"),
            rx.el.span("A coordinar"),
            class_name="ui-cart__row",
        ),
        rx.el.div(
            rx.el.span("Total"),
            rx.el.span(CheckoutEstado.subtotal),
            class_name="ui-cart__row ui-cart__row--total",
        ),
        rx.el.p(
            "No se cobra el envio en esta version: se coordina despues de confirmar.",
            class_name="ui-checkout__note",
        ),
        class_name="ui-cart__summary",
    )


def _esqueletos() -> rx.Component:
    return rx.el.div(
        Skeleton("block", height="320px"),
        Skeleton("block", height="240px"),
        class_name="ui-checkout",
        **{"aria-hidden": "true"},
    )


def _error() -> rx.Component:
    return rx.el.div(
        Alert(
            title="No pudimos cargar el checkout",
            description=CheckoutEstado.error,
            tone="error",
        ),
        Button(
            "Reintentar",
            variant="secondary",
            on_click=CheckoutEstado.reintentar,
        ),
        class_name="ui-stack",
    )


def _confirmacion() -> rx.Component:
    """Order confirmation: number, total and where it goes (D-005)."""
    return Card(
        rx.el.div(
            Alert(
                title="Pedido confirmado",
                description="Te vamos a contactar para coordinar la entrega.",
                tone="success",
            ),
            rx.el.p(
                "Pedido #" + CheckoutEstado.pedido_id.to_string(),
                class_name="ui-checkout__order",
            ),
            rx.el.dl(
                rx.el.div(
                    rx.el.dt("Total"),
                    rx.el.dd(CheckoutEstado.total_confirmado),
                    class_name="ui-cart__row",
                ),
                rx.el.div(
                    rx.el.dt("Entrega"),
                    rx.el.dd(CheckoutEstado.entrega_confirmada),
                    class_name="ui-cart__row",
                ),
                class_name="ui-checkout__details",
            ),
            ButtonLink("Volver al catalogo", href="/"),
            class_name="ui-checkout__success",
        ),
        class_name="ui-checkout__card",
    )


def _contenido() -> Any:
    return rx.cond(
        CheckoutEstado.confirmado,
        _confirmacion(),
        rx.cond(
            CheckoutEstado.cargando,
            _esqueletos(),
            rx.cond(
                CheckoutEstado.error != "",
                _error(),
                rx.el.div(
                    rx.cond(
                        CheckoutEstado.error_confirmacion != "",
                        Alert(
                            title="No pudimos confirmar el pedido",
                            description=CheckoutEstado.error_confirmacion,
                            tone="error",
                        ),
                        rx.fragment(),
                    ),
                    rx.el.div(_formulario(), _resumen(), class_name="ui-checkout"),
                    class_name="ui-stack",
                ),
            ),
        ),
    )


@rx.page(route="/checkout", title="Finalizar compra", on_load=CheckoutEstado.on_load)
def checkout_pagina() -> rx.Component:
    return AppShell(
        Container(
            PageHeader("Finalizar compra", CheckoutEstado.resumen),
            _contenido(),
            class_name="ui-stack",
        ),
        nav=nav_de_cuenta(),
    )
