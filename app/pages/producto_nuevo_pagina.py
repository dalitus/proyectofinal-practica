"""Alta de un producto en ``/admin/productos/nuevo`` (T-050, D-049).

Los campos del producto se cargan en el formulario y las variantes se agregan a
una lista pendiente: nada toca la base hasta "Crear producto", y ese guardado es
una sola transaccion con el producto y todas sus variantes.

Es una pantalla distinta de la edicion a proposito: el problema original era un
formulario que servia para las dos cosas y abria el modal equivocado.
"""

from __future__ import annotations

from typing import Any

import reflex as rx

from app.pages.cuenta_menu import nav_de_cuenta
from app.state.productos_admin_estado import ProductoNuevoEstado
from app.ui import (
    AdminTabs,
    Alert,
    AppShell,
    Button,
    ButtonLink,
    Card,
    Container,
    ImageField,
    Input,
    PageHeader,
    Select,
    src_de_imagen,
)


def _descripcion() -> rx.Component:
    return rx.el.div(
        rx.el.label(
            "Descripcion",
            **{"html_for": "producto-descripcion"},
            class_name="ui-field__label",
        ),
        rx.el.textarea(
            id="producto-descripcion",
            value=ProductoNuevoEstado.descripcion,
            on_change=ProductoNuevoEstado.escribir_campo("descripcion"),
            rows="4",
            max_length=255,
            class_name="ui-input ui-textarea",
            **{
                "aria-invalid": ProductoNuevoEstado.errores.get("descripcion", "") != "",
            },
        ),
        rx.cond(
            ProductoNuevoEstado.errores.get("descripcion", "") != "",
            rx.el.span(
                ProductoNuevoEstado.errores.get("descripcion", ""),
                class_name="ui-field__error",
                role="alert",
            ),
            rx.fragment(),
        ),
        class_name="ui-field ui-form-grid__full",
    )


def _campos() -> rx.Component:
    return Card(
        rx.el.h2("Datos del producto", class_name="ui-text"),
        rx.el.div(
            Input(
                label="Nombre",
                value=ProductoNuevoEstado.nombre,
                on_change=ProductoNuevoEstado.escribir_campo("nombre"),
                error=ProductoNuevoEstado.errores.get("nombre", ""),
                placeholder="Zapatilla urbana",
                input_id="producto-nombre",
            ),
            Input(
                label="Marca",
                value=ProductoNuevoEstado.marca,
                on_change=ProductoNuevoEstado.escribir_campo("marca"),
                error=ProductoNuevoEstado.errores.get("marca", ""),
                placeholder="Fermin",
                input_id="producto-marca",
            ),
            Input(
                label="Precio (ARS)",
                value=ProductoNuevoEstado.precio,
                on_change=ProductoNuevoEstado.escribir_campo("precio"),
                error=ProductoNuevoEstado.errores.get("precio", ""),
                placeholder="45000",
                input_id="producto-precio",
            ),
            Select(
                label="Categoria",
                opciones=ProductoNuevoEstado.categorias,
                value=ProductoNuevoEstado.categoria_id,
                on_change=ProductoNuevoEstado.escribir_campo("categoria_id"),
                error=ProductoNuevoEstado.errores.get("categoria_id", ""),
                placeholder="Elegi una categoria",
                input_id="producto-categoria",
            ),
            _descripcion(),
            ImageField(
                upload_id="producto-imagen-nuevo",
                on_drop=ProductoNuevoEstado.subir_imagen,
                on_clear=ProductoNuevoEstado.quitar_imagen,
                preview=src_de_imagen(ProductoNuevoEstado.imagen),
                error=ProductoNuevoEstado.error_imagen,
            ),
            class_name="ui-form-grid",
        ),
        class_name="ui-stack",
    )


def _fila_pendiente(variante: Any, indice: Any) -> rx.Component:
    return rx.el.tr(
        rx.el.td(variante["color"]),
        rx.el.td(variante["talle"]),
        rx.el.td(variante["cantidad"], class_name="ui-table__num"),
        rx.el.td(
            Button(
                "Quitar",
                variant="ghost",
                on_click=ProductoNuevoEstado.quitar_variante(indice),
            ),
            class_name="ui-table__actions",
        ),
        class_name="ui-table__row",
    )


def _pendientes() -> rx.Component:
    return rx.cond(
        ProductoNuevoEstado.hay_variantes,
        rx.el.div(
            rx.el.table(
                rx.el.thead(
                    rx.el.tr(
                        rx.el.th("Color"),
                        rx.el.th("Talle"),
                        rx.el.th("Stock", class_name="ui-table__num"),
                        rx.el.th("", class_name="ui-table__actions"),
                    )
                ),
                rx.el.tbody(
                    rx.foreach(ProductoNuevoEstado.variantes, _fila_pendiente)
                ),
                class_name="ui-table",
            ),
            class_name="ui-table-wrap",
        ),
        rx.el.p(
            "Todavia no agregaste variantes. Un producto sin variantes no se "
            "puede comprar.",
            class_name="ui-text ui-text--muted ui-text--small",
        ),
    )


def _agregar_variante() -> rx.Component:
    return rx.el.div(
        Input(
            label="Color",
            value=ProductoNuevoEstado.nuevo_color,
            on_change=ProductoNuevoEstado.escribir_campo("nuevo_color"),
            placeholder="Negro",
            input_id="producto-variante-color",
        ),
        Input(
            label="Talle",
            value=ProductoNuevoEstado.nuevo_talle,
            on_change=ProductoNuevoEstado.escribir_campo("nuevo_talle"),
            placeholder="38",
            input_id="producto-variante-talle",
        ),
        Input(
            label="Stock",
            type="text",
            value=ProductoNuevoEstado.nuevo_cantidad,
            on_change=ProductoNuevoEstado.escribir_campo("nuevo_cantidad"),
            input_id="producto-variante-stock",
            inputmode="numeric",
        ),
        Button(
            "Agregar variante",
            variant="secondary",
            on_click=ProductoNuevoEstado.agregar_variante,
        ),
        class_name="ui-variant-add",
    )


def _variantes() -> rx.Component:
    return Card(
        rx.el.h2("Variantes", class_name="ui-text"),
        rx.el.p(
            "Cada variante es una combinacion de color y talle con su propio "
            "stock. La misma combinacion no puede repetirse.",
            class_name="ui-text ui-text--muted ui-text--small",
        ),
        _pendientes(),
        _agregar_variante(),
        rx.cond(
            ProductoNuevoEstado.error_variante != "",
            rx.el.span(
                ProductoNuevoEstado.error_variante,
                class_name="ui-field__error",
                role="alert",
            ),
            rx.fragment(),
        ),
        class_name="ui-stack",
    )


def _acciones() -> rx.Component:
    return rx.el.div(
        Button("Crear producto", on_click=ProductoNuevoEstado.guardar),
        ButtonLink("Cancelar", href="/admin/productos", variant="ghost"),
        class_name="ui-admin__actions",
    )


def _contenido() -> Any:
    return rx.cond(
        ProductoNuevoEstado.error != "",
        Alert(
            title="No pudimos cargar las categorias",
            description=ProductoNuevoEstado.error,
            tone="error",
        ),
        rx.el.div(
            rx.cond(
                ProductoNuevoEstado.errores.get("formulario", "") != "",
                Alert(
                    title="No pudimos crear el producto",
                    description=ProductoNuevoEstado.errores.get("formulario", ""),
                    tone="error",
                ),
                rx.fragment(),
            ),
            _campos(),
            _variantes(),
            _acciones(),
            class_name="ui-stack",
        ),
    )


@rx.page(
    route="/admin/productos/nuevo",
    title="Nuevo producto",
    on_load=ProductoNuevoEstado.on_load,
)
def producto_nuevo_pagina() -> rx.Component:
    return AppShell(
        Container(
            rx.el.a(
                "Volver a productos",
                href="/admin/productos",
                class_name="ui-back",
            ),
            PageHeader("Nuevo producto"),
            AdminTabs(active="productos"),
            _contenido(),
            class_name="ui-stack",
        ),
        nav=nav_de_cuenta(cart=False),
    )
