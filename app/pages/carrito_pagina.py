"""Carrito en ``/carrito`` (T-040, design.md 5).

Solo composicion: las lineas, los subtotales y el total llegan ya calculados y
formateados del servicio. Un unico CTA primario ("Ir a pagar"); el resto son
acciones secundarias o ghost (design.md 6).
"""

from __future__ import annotations

from typing import Any

import reflex as rx

from app.pages.cuenta_menu import nav_de_cuenta
from app.state.carrito_estado import CarritoEstado
from app.ui import (
    Alert,
    AppShell,
    Button,
    ButtonLink,
    ConfirmDialog,
    Container,
    EmptyState,
    PageHeader,
    Skeleton,
    src_de_imagen,
)

# Misma forma que una linea real: miniatura alta y tres renglones.
ESQUELETOS_AL_CARGAR = 3


def _miniatura(linea: Any) -> rx.Component:
    """3:4 thumbnail; the placeholder keeps the box when there is no photo."""
    return rx.el.div(
        rx.cond(
            linea["imagen"] != "",
            rx.image(
                src=src_de_imagen(linea["imagen"]),
                alt=linea["nombre"],
                loading="lazy",
                class_name="ui-cart__image",
            ),
            rx.el.div("Sin imagen", class_name="ui-cart__placeholder"),
        ),
        class_name="ui-cart__thumb",
    )


def _stepper(linea: Any) -> rx.Component:
    """QuantityStepper: the plus stops at the variant's stock (design.md 4.3)."""
    return rx.el.div(
        Button(
            "-",
            variant="ghost",
            on_click=CarritoEstado.restar(linea["id"]),
            **{"aria-label": "Quitar una unidad de " + linea["nombre"].to_string(use_json=False)},
        ),
        rx.el.span(
            linea["cantidad"],
            class_name="ui-stepper__qty",
            **{"aria-live": "polite"},
        ),
        Button(
            "+",
            variant="ghost",
            on_click=CarritoEstado.sumar(linea["id"]),
            disabled=linea["cantidad"].to(int) >= linea["stock_disponible"].to(int),
            **{"aria-label": "Agregar una unidad de " + linea["nombre"].to_string(use_json=False)},
        ),
        class_name="ui-stepper",
    )


def _linea(linea: Any) -> rx.Component:
    """CartLine: thumbnail, name, variant, unit price, stepper and subtotal."""
    return rx.el.article(
        _miniatura(linea),
        rx.el.div(
            rx.el.a(
                linea["nombre"],
                href="/producto/" + linea["producto_id"].to_string(),
                class_name="ui-cart__name",
            ),
            rx.el.p(
                "Color "
                + linea["color"].to_string(use_json=False)
                + " · Talle "
                + linea["talle"].to_string(use_json=False),
                class_name="ui-text ui-text--muted ui-text--small",
            ),
            rx.el.p(
                linea["precio_unitario"].to_string(use_json=False) + " cada uno",
                class_name="ui-text ui-text--muted ui-text--small",
            ),
            class_name="ui-cart__info",
        ),
        rx.el.div(
            _stepper(linea),
            rx.el.p(linea["subtotal"], class_name="ui-cart__subtotal"),
            Button(
                "Quitar",
                variant="ghost",
                on_click=CarritoEstado.quitar(linea["id"]),
                **{
                    "aria-label": "Quitar "
                    + linea["nombre"].to_string(use_json=False)
                    + " del carrito"
                },
            ),
            class_name="ui-cart__footer",
        ),
        class_name="ui-cart__line",
    )


def _resumen() -> rx.Component:
    """OrderSummary: sticky from 1024px, one primary CTA (design.md 5)."""
    return rx.el.aside(
        rx.el.h2("Resumen", class_name="ui-cart__summary-title"),
        rx.el.div(
            rx.el.span("Subtotal"),
            rx.el.span(CarritoEstado.subtotal),
            class_name="ui-cart__row",
        ),
        rx.el.div(
            rx.el.span("Envio"),
            rx.el.span("A coordinar"),
            class_name="ui-cart__row",
        ),
        rx.el.div(
            rx.el.span("Total"),
            rx.el.span(CarritoEstado.subtotal),
            class_name="ui-cart__row ui-cart__row--total",
        ),
        ButtonLink("Ir a pagar", href="/checkout", variant="primary"),
        ButtonLink("Seguir comprando", href="/", variant="ghost"),
        class_name="ui-cart__summary",
    )


def _lineas() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            ConfirmDialog(
                trigger=Button("Vaciar carrito", variant="ghost"),
                title="Vaciar el carrito",
                description="Se quitan todos los productos. Esta accion no se puede deshacer.",
                confirm_label="Vaciar",
                on_confirm=CarritoEstado.vaciar,
            ),
            class_name="ui-cart__toolbar",
        ),
        rx.foreach(CarritoEstado.lineas, _linea),
        class_name="ui-cart__lines",
    )


def _carrito() -> rx.Component:
    return rx.el.div(_lineas(), _resumen(), class_name="ui-cart")


def _esqueletos() -> rx.Component:
    return rx.el.div(
        *[
            rx.el.div(
                Skeleton("block", height="100%"),
                Skeleton("line", width="60%"),
                Skeleton("line", width="40%"),
                class_name="ui-cart__line",
            )
            for _ in range(ESQUELETOS_AL_CARGAR)
        ],
        class_name="ui-cart__lines",
        **{"aria-hidden": "true"},
    )


def _error() -> rx.Component:
    return rx.el.div(
        Alert(
            title="No pudimos cargar el carrito",
            description=CarritoEstado.error,
            tone="error",
        ),
        Button(
            "Reintentar",
            variant="secondary",
            on_click=CarritoEstado.reintentar,
        ),
        class_name="ui-stack",
    )


def _vacio() -> rx.Component:
    return EmptyState(
        "Tu carrito esta vacio",
        "Cuando agregues productos, los vas a ver aca.",
        action=ButtonLink("Ver catalogo", href="/"),
    )


def _contenido() -> Any:
    return rx.cond(
        CarritoEstado.cargando,
        _esqueletos(),
        rx.cond(
            CarritoEstado.error != "",
            _error(),
            rx.cond(
                CarritoEstado.vacio,
                _vacio(),
                _carrito(),
            ),
        ),
    )


@rx.page(route="/carrito", title="Carrito", on_load=CarritoEstado.on_load)
def carrito_pagina() -> rx.Component:
    return AppShell(
        Container(
            PageHeader("Carrito", CarritoEstado.resumen),
            _contenido(),
            class_name="ui-stack",
        ),
        nav=nav_de_cuenta(),
    )
