import reflex as rx
from proyectofinal.state.carrito_state import CarritoState
from proyectofinal.pages.ui_helpers import PrimaryButton, SecondaryButton, DangerButton, Card, PageHeader


def producto_en_carrito_card(p: dict) -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.image(
                src=p.get("imagen", "/static/default.jpg"),
                alt=p.get("nombre", ""),
                width="120px",
                height="120px",
                object_fit="cover",
                border_radius="8px"
            ),
            rx.vstack(
                rx.text(p["nombre"], font_weight="bold", font_size="1.2em"),
                rx.text(f"Precio unitario: ${p['precio']}"),
                rx.text(f"Cantidad: {p['cantidad']}"),
                rx.text(f"Subtotal: ${p['subtotal']}"),
                SecondaryButton("🗑️ Eliminar uno", on_click=CarritoState.eliminar_producto(p["id_producto"])),
                spacing="2"
            ),
            spacing="4",
            align_items="center"
        ),
        width="100%",
        padding="15px",
        margin_y="10px",
        box_shadow="md",
        border_radius="10px"
    )


def modal_ubicacion() -> rx.Component:
    """Modal emergente para solicitar datos de ubicación"""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("📍 Datos de Entrega"),
            rx.dialog.description(
                rx.vstack(
                    rx.heading("Completa tus datos de entrega", size="4"),
                    rx.vstack(
                        rx.text("Dirección *"),
                        rx.input(
                            placeholder="Calle y número",
                            value=CarritoState.direccion,
                            on_change=CarritoState.set_direccion,
                            width="100%"
                        ),
                        rx.hstack(
                            rx.vstack(
                                rx.text("Número"),
                                rx.input(
                                    placeholder="Número",
                                    value=CarritoState.numero,
                                    on_change=CarritoState.set_numero,
                                    width="100%"
                                )
                            ),
                            rx.vstack(
                                rx.text("Departamento"),
                                rx.input(
                                    placeholder="Ej: Apto 5",
                                    value=CarritoState.departamento,
                                    on_change=CarritoState.set_departamento,
                                    width="100%"
                                )
                            ),
                            width="100%"
                        ),
                        rx.hstack(
                            rx.vstack(
                                rx.text("Código Postal"),
                                rx.input(
                                    placeholder="Código postal",
                                    value=CarritoState.codigo_postal,
                                    on_change=CarritoState.set_codigo_postal,
                                    width="100%"
                                )
                            ),
                            rx.vstack(
                                rx.text("Ciudad *"),
                                rx.input(
                                    placeholder="Ciudad",
                                    value=CarritoState.ciudad,
                                    on_change=CarritoState.set_ciudad,
                                    width="100%"
                                )
                            ),
                            width="100%"
                        ),
                        rx.vstack(
                            rx.text("Provincia/Región *"),
                            rx.input(
                                placeholder="Provincia",
                                value=CarritoState.provincia,
                                on_change=CarritoState.set_provincia,
                                width="100%"
                            )
                        ),
                        spacing="4",
                        width="100%"
                    ),
                    spacing="6",
                    width="100%"
                )
            ),
            rx.hstack(
                SecondaryButton(
                    "Cancelar",
                    on_click=CarritoState.cerrar_modal_ubicacion
                ),
                PrimaryButton(
                    "Confirmar Compra",
                    on_click=CarritoState.finalizar_compra_con_ubicacion
                ),
                spacing="4"
            )
        ),
        open=CarritoState.mostrar_modal_ubicacion,
        on_open_change=CarritoState.cerrar_modal_ubicacion
    )


@rx.page(route="/carrito", on_load=CarritoState.cargar_carrito_agrupado)
def carrito_page() -> rx.Component:
    return rx.center(
        rx.vstack(
            modal_ubicacion(),
            PageHeader("🛒 Tu Carrito", "Revisa tu selección y finaliza la compra"),
            rx.cond(
                CarritoState.mensaje_compra != "",
                rx.box(
                    rx.text(CarritoState.mensaje_compra),
                    background_color=rx.cond(
                        CarritoState.mensaje_compra.contains("Error"),
                        "red.100",
                        "green.100"
                    ),
                    border=rx.cond(
                        CarritoState.mensaje_compra.contains("Error"),
                        "1px solid red",
                        "1px solid green"
                    ),
                    border_radius="md",
                    padding="10px",
                    width="100%"
                ),
                rx.box()
            ),
            rx.divider(),
            rx.cond(
                CarritoState.productos_agrupados.length() == 0,
                rx.text("Tu carrito está vacío."),
                rx.vstack(
                    rx.foreach(
                        CarritoState.productos_agrupados.to(list[dict]),
                        producto_en_carrito_card
                    ),
                    spacing="4",
                    width="100%"
                )
            ),
            rx.divider(),
            rx.hstack(
                rx.text(f"🧮 Total: ${CarritoState.total}", font_size="1.2em", font_weight="bold"),
                rx.spacer(),
                rx.text(f"🧺 Productos: {CarritoState.productos_agrupados.length()}", font_size="1em"),
                width="100%"
            ),
            rx.hstack(
                DangerButton("Vaciar Carrito", on_click=CarritoState.vaciar_carrito_completo),
                PrimaryButton("Finalizar Compra", on_click=CarritoState.abrir_modal_ubicacion),
                spacing="4"
            ),
            spacing="6",
            padding="30px",
            width="90%"
        )
    )