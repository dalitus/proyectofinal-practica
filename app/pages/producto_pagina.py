"""Detalle de producto en ``/producto/[producto_id]`` (T-031).

La ruta lleva el id (D-024), asi que recargar o abrir el link directo muestra el
mismo producto: nada depende de una seleccion en memoria.

Solo composicion: el precio llega formateado del servicio, los talles ya vienen
con su disponibilidad y aca no hay un solo color, sombra o tamano suelto. La
pantalla tiene un proposito: elegir talle (design.md 1).
"""

from __future__ import annotations

from typing import Any

import reflex as rx

from app.state.carrito_estado import CarritoEstado
from app.state.detalle_estado import DetalleEstado
from app.ui import (
    Alert,
    AppShell,
    Badge,
    Button,
    ButtonLink,
    Container,
    EmptyState,
    SizeChip,
    Skeleton,
)


def _volver() -> rx.Component:
    """Way back to the catalog: the detail is never a dead end."""
    return rx.el.a("Volver al catalogo", href="/", class_name="ui-back")


def _media() -> rx.Component:
    """3:4 image on ``surface``; the placeholder keeps the box when there is no photo."""
    return rx.el.div(
        rx.cond(
            DetalleEstado.producto["imagen"] != "",
            rx.image(
                src=DetalleEstado.producto["imagen"],
                alt=DetalleEstado.producto["nombre"],
                class_name="ui-detail__image",
            ),
            rx.el.div("Sin imagen", class_name="ui-detail__placeholder"),
        ),
        class_name="ui-detail__media",
    )


def _estado_de_stock() -> rx.Component:
    """Badge for the chosen variant, not for the product as a whole (D-009)."""
    return rx.match(
        DetalleEstado.stock_estado,
        ("sin_stock", Badge("Sin stock", tone="danger", quiet=True)),
        ("ultimas", Badge(DetalleEstado.stock_etiqueta, tone="info", quiet=True)),
        Badge("Disponible", tone="success", quiet=True),
    )


def _comprar() -> rx.Component:
    """Primary CTA: adds the chosen variant, not the product (D-009).

    A guest is sent to the login and comes back here (D-002); the cart state owns
    that decision, so the page does not branch on the session.
    """
    return rx.el.div(
        Button(
            "Agregar al carrito",
            on_click=CarritoEstado.agregar(DetalleEstado.variante_id, 1),
            disabled=~DetalleEstado.puede_comprar,
        ),
        rx.cond(
            DetalleEstado.puede_comprar,
            rx.fragment(),
            rx.el.p(
                "Elegi otro talle para poder comprar.",
                class_name="ui-text ui-text--muted ui-text--small",
            ),
        ),
        class_name="ui-detail__buy",
    )


def _colores() -> rx.Component:
    return rx.el.div(
        rx.el.p("Color", class_name="ui-detail__group-label"),
        rx.el.div(
            rx.foreach(
                DetalleEstado.colores,
                lambda color: SizeChip(
                    color,
                    selected=DetalleEstado.color == color,
                    on_click=DetalleEstado.elegir_color(color),
                ),
            ),
            class_name="ui-detail__chips",
        ),
        class_name="ui-detail__group",
    )


def _talles() -> rx.Component:
    """Full size scale with the sold-out sizes disabled, never hidden."""
    return rx.el.div(
        rx.el.p("Talle", class_name="ui-detail__group-label"),
        rx.el.div(
            rx.foreach(
                DetalleEstado.talles_del_color,
                lambda talle: SizeChip(
                    talle["talle"],
                    selected=DetalleEstado.talle == talle["talle"],
                    disabled=talle["agotado"],
                    on_click=DetalleEstado.elegir_talle(talle["talle"]),
                ),
            ),
            class_name="ui-detail__chips",
        ),
        class_name="ui-detail__group",
    )


def _descripcion() -> rx.Component:
    return rx.cond(
        DetalleEstado.producto["descripcion"] != "",
        rx.el.div(
            rx.el.p("Descripcion", class_name="ui-detail__group-label"),
            rx.el.p(
                DetalleEstado.producto["descripcion"],
                class_name="ui-detail__description",
            ),
            class_name="ui-stack",
        ),
        rx.fragment(),
    )


def _info() -> rx.Component:
    """Brand, name, price, the two pickers and the stock of the chosen variant."""
    return rx.el.div(
        rx.cond(
            DetalleEstado.producto["marca"] != "",
            rx.el.p(
                DetalleEstado.producto["marca"],
                class_name="ui-text ui-text--muted ui-text--small",
            ),
            rx.fragment(),
        ),
        rx.el.h1(DetalleEstado.producto["nombre"], class_name="ui-detail__name"),
        rx.el.p(DetalleEstado.producto["precio"], class_name="ui-detail__price"),
        rx.cond(
            DetalleEstado.producto["categoria"] != "",
            rx.el.p(
                DetalleEstado.producto["categoria"],
                class_name="ui-text ui-text--muted ui-text--small",
            ),
            rx.fragment(),
        ),
        _colores(),
        _talles(),
        rx.el.div(_estado_de_stock(), class_name="ui-row"),
        rx.el.p(
            DetalleEstado.stock_etiqueta,
            class_name="ui-visually-hidden",
            role="status",
            **{"aria-live": "polite"},
        ),
        _comprar(),
        _descripcion(),
        class_name="ui-detail__info",
    )


def _detalle() -> rx.Component:
    return rx.el.div(_media(), _info(), class_name="ui-detail")


def _esqueleto() -> rx.Component:
    """Same shape as the content: a large block and four lines."""
    return rx.el.div(
        rx.el.div(
            Skeleton("block", height="100%"),
            class_name="ui-detail__media",
        ),
        rx.el.div(
            Skeleton("line", width="35%"),
            Skeleton("line", width="75%"),
            Skeleton("line", width="25%"),
            Skeleton("line", width="100%"),
            class_name="ui-detail__info",
            **{"aria-hidden": "true"},
        ),
        class_name="ui-detail",
    )


def _error() -> rx.Component:
    return rx.el.div(
        Alert(
            title="No pudimos cargar el producto",
            description=DetalleEstado.error,
            tone="error",
        ),
        Button(
            "Reintentar",
            variant="secondary",
            on_click=DetalleEstado.reintentar,
        ),
        class_name="ui-stack",
    )


def _no_encontrado() -> rx.Component:
    return EmptyState(
        "No encontramos ese producto",
        "Puede que ya no este disponible. Mira el catalogo completo.",
        action=ButtonLink("Ver catalogo", href="/"),
    )


def _contenido() -> Any:
    return rx.cond(
        DetalleEstado.cargando,
        _esqueleto(),
        rx.cond(
            DetalleEstado.error != "",
            _error(),
            rx.cond(
                DetalleEstado.no_encontrado,
                _no_encontrado(),
                _detalle(),
            ),
        ),
    )


@rx.page(
    route="/producto/[producto_id]",
    title=DetalleEstado.nombre,
    on_load=DetalleEstado.on_load,
)
def producto_pagina() -> rx.Component:
    return AppShell(
        Container(
            _volver(),
            _contenido(),
            class_name="ui-stack",
        )
    )
