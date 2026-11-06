"""Edicion de un producto en ``/admin/productos/[producto_id]`` (T-050, D-049).

Tres bloques con acciones independientes: los campos del producto, las
variantes (una fila por combinacion, con guardar y eliminar propios) y el estado
del producto (desactivar o reactivar, con confirmacion).

Desactivar es un borrado logico (D-028): el producto sale del catalogo y las
variantes quedan, para que reactivarlo recupere su stock.
"""

from __future__ import annotations

from typing import Any

import reflex as rx

from app.pages.cuenta_menu import nav_de_cuenta
from app.state.productos_admin_estado import ProductoEditarEstado
from app.ui import (
    AdminTabs,
    Alert,
    AppShell,
    Badge,
    Button,
    ButtonLink,
    Card,
    ConfirmDialog,
    Container,
    EmptyState,
    ImageField,
    Input,
    PageHeader,
    Select,
    Skeleton,
    src_de_imagen,
)


def _volver() -> rx.Component:
    return rx.el.a(
        "Volver a productos",
        href="/admin/productos",
        class_name="ui-back",
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
            value=ProductoEditarEstado.descripcion,
            on_change=ProductoEditarEstado.escribir_campo("descripcion"),
            rows="4",
            max_length=255,
            class_name="ui-input ui-textarea",
            **{
                "aria-invalid": ProductoEditarEstado.errores.get("descripcion", "") != "",
            },
        ),
        rx.cond(
            ProductoEditarEstado.errores.get("descripcion", "") != "",
            rx.el.span(
                ProductoEditarEstado.errores.get("descripcion", ""),
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
                value=ProductoEditarEstado.nombre,
                on_change=ProductoEditarEstado.escribir_campo("nombre"),
                error=ProductoEditarEstado.errores.get("nombre", ""),
                input_id="producto-nombre",
            ),
            Input(
                label="Marca",
                value=ProductoEditarEstado.marca,
                on_change=ProductoEditarEstado.escribir_campo("marca"),
                error=ProductoEditarEstado.errores.get("marca", ""),
                input_id="producto-marca",
            ),
            Input(
                label="Precio (ARS)",
                value=ProductoEditarEstado.precio,
                on_change=ProductoEditarEstado.escribir_campo("precio"),
                error=ProductoEditarEstado.errores.get("precio", ""),
                input_id="producto-precio",
            ),
            Select(
                label="Categoria",
                opciones=ProductoEditarEstado.categorias,
                value=ProductoEditarEstado.categoria_id,
                on_change=ProductoEditarEstado.escribir_campo("categoria_id"),
                error=ProductoEditarEstado.errores.get("categoria_id", ""),
                placeholder="Elegi una categoria",
                input_id="producto-categoria",
            ),
            _descripcion(),
            ImageField(
                upload_id="producto-imagen-editar",
                on_drop=ProductoEditarEstado.subir_imagen,
                on_clear=ProductoEditarEstado.quitar_imagen,
                preview=src_de_imagen(ProductoEditarEstado.imagen),
                error=ProductoEditarEstado.error_imagen,
            ),
            class_name="ui-form-grid",
        ),
        rx.cond(
            ProductoEditarEstado.errores.get("formulario", "") != "",
            Alert(
                title="No pudimos guardar el producto",
                description=ProductoEditarEstado.errores.get("formulario", ""),
                tone="error",
            ),
            rx.fragment(),
        ),
        Button(
            "Guardar cambios",
            on_click=ProductoEditarEstado.guardar_campos,
        ),
        class_name="ui-stack",
    )


def _fila_variante(variante: Any) -> rx.Component:
    identificador = variante["id"]
    return rx.el.div(
        rx.el.div(
            Input(
                label="Color",
                value=variante["color"],
                on_change=ProductoEditarEstado.escribir_variante(identificador, "color"),
                input_id="variante-color-" + identificador.to_string(),
            ),
            Input(
                label="Talle",
                value=variante["talle"],
                on_change=ProductoEditarEstado.escribir_variante(identificador, "talle"),
                input_id="variante-talle-" + identificador.to_string(),
            ),
            Input(
                label="Stock",
                type="text",
                value=variante["cantidad"],
                on_change=ProductoEditarEstado.escribir_variante(identificador, "cantidad"),
                input_id="variante-stock-" + identificador.to_string(),
                inputmode="numeric",
            ),
            rx.el.div(
                Button(
                    "Guardar",
                    variant="secondary",
                    on_click=ProductoEditarEstado.guardar_variante(identificador),
                ),
                ConfirmDialog(
                    trigger=Button("Eliminar", variant="ghost"),
                    title="Eliminar la variante",
                    description=(
                        "Se borra esta combinacion de color y talle. Si la "
                        "variante ya tiene pedidos, no se puede eliminar: dejala "
                        "con stock 0."
                    ),
                    confirm_label="Eliminar variante",
                    on_confirm=ProductoEditarEstado.eliminar_variante(identificador),
                ),
                class_name="ui-variant-row__actions",
            ),
            class_name="ui-variant-row",
        ),
        rx.cond(
            ProductoEditarEstado.error_variante_id == identificador,
            rx.el.span(
                ProductoEditarEstado.error_variante,
                class_name="ui-variant-row__error",
                role="alert",
            ),
            rx.fragment(),
        ),
    )


def _agregar_variante() -> rx.Component:
    return rx.el.div(
        Input(
            label="Color",
            value=ProductoEditarEstado.nuevo_color,
            on_change=ProductoEditarEstado.escribir_campo("nuevo_color"),
            input_id="variante-nueva-color",
        ),
        Input(
            label="Talle",
            value=ProductoEditarEstado.nuevo_talle,
            on_change=ProductoEditarEstado.escribir_campo("nuevo_talle"),
            input_id="variante-nueva-talle",
        ),
        Input(
            label="Stock",
            type="text",
            value=ProductoEditarEstado.nuevo_cantidad,
            on_change=ProductoEditarEstado.escribir_campo("nuevo_cantidad"),
            input_id="variante-nueva-stock",
            inputmode="numeric",
        ),
        Button(
            "Agregar variante",
            variant="secondary",
            on_click=ProductoEditarEstado.agregar_variante,
        ),
        class_name="ui-variant-add",
    )


def _variantes() -> rx.Component:
    return Card(
        rx.el.h2("Variantes", class_name="ui-text"),
        rx.el.p(
            ProductoEditarEstado.resumen_variantes
            + " con stock propio. Edita una fila y guardala por separado.",
            class_name="ui-text ui-text--muted ui-text--small",
        ),
        rx.cond(
            ProductoEditarEstado.hay_variantes,
            rx.el.div(
                rx.foreach(ProductoEditarEstado.variantes, _fila_variante),
            ),
            rx.el.p(
                "Este producto no tiene variantes: nadie puede comprarlo.",
                class_name="ui-text ui-text--muted ui-text--small",
            ),
        ),
        _agregar_variante(),
        rx.cond(
            ProductoEditarEstado.error_alta != "",
            rx.el.span(
                ProductoEditarEstado.error_alta,
                class_name="ui-field__error",
                role="alert",
            ),
            rx.fragment(),
        ),
        class_name="ui-stack",
    )


def _estado_del_producto() -> rx.Component:
    return Card(
        rx.el.h2("Estado del producto", class_name="ui-text"),
        rx.cond(
            ProductoEditarEstado.activo,
            rx.el.div(
                rx.el.p(
                    "El producto esta publicado en el catalogo. Desactivarlo lo "
                    "saca de la tienda sin borrar sus variantes ni sus pedidos.",
                    class_name="ui-text ui-text--muted ui-text--small",
                ),
                ConfirmDialog(
                    trigger=Button("Desactivar producto", variant="danger"),
                    title="Desactivar el producto",
                    description=(
                        "Deja de aparecer en el catalogo. Las variantes y el "
                        "historial de pedidos se conservan."
                    ),
                    confirm_label="Desactivar",
                    on_confirm=ProductoEditarEstado.desactivar,
                ),
                class_name="ui-admin__actions",
            ),
            rx.el.div(
                rx.el.p(
                    "El producto esta desactivado: no aparece en el catalogo.",
                    class_name="ui-text ui-text--muted ui-text--small",
                ),
                Button(
                    "Reactivar producto",
                    variant="secondary",
                    on_click=ProductoEditarEstado.reactivar,
                ),
                class_name="ui-admin__actions",
            ),
        ),
        class_name="ui-stack",
    )


def _esqueletos() -> rx.Component:
    return rx.el.div(
        Skeleton("block", height="220px"),
        Skeleton("block", height="220px"),
        class_name="ui-stack",
        **{"aria-hidden": "true"},
    )


def _no_encontrado() -> rx.Component:
    return EmptyState(
        "Ese producto no existe",
        "Puede que se haya borrado o que el link este mal.",
        action=ButtonLink("Ver todos los productos", href="/admin/productos"),
    )


def _error() -> rx.Component:
    return rx.el.div(
        Alert(
            title="No pudimos cargar el producto",
            description=ProductoEditarEstado.error,
            tone="error",
        ),
        Button(
            "Reintentar",
            variant="secondary",
            on_click=ProductoEditarEstado.reintentar,
        ),
        class_name="ui-stack",
    )


def _contenido() -> Any:
    return rx.cond(
        ProductoEditarEstado.cargando,
        _esqueletos(),
        rx.cond(
            ProductoEditarEstado.error != "",
            _error(),
            rx.cond(
                ProductoEditarEstado.no_encontrado,
                _no_encontrado(),
                rx.el.div(
                    _campos(),
                    _variantes(),
                    _estado_del_producto(),
                    class_name="ui-stack",
                ),
            ),
        ),
    )


@rx.page(
    route="/admin/productos/[producto_id]",
    title="Producto",
    on_load=ProductoEditarEstado.on_load,
)
def producto_admin_pagina() -> rx.Component:
    return AppShell(
        Container(
            _volver(),
            PageHeader(
                ProductoEditarEstado.titulo,
                actions=rx.cond(
                    ProductoEditarEstado.activo,
                    Badge("Activo", tone="success", quiet=True),
                    Badge("Inactivo", tone="neutral", quiet=True),
                ),
            ),
            AdminTabs(active="productos"),
            _contenido(),
            class_name="ui-stack",
        ),
        nav=nav_de_cuenta(cart=False),
    )
