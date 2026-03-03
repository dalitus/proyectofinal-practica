import reflex as rx
from proyectofinal.state.catalogo_state import CatalogoState
from proyectofinal.state.users_state import UsersState
from proyectofinal.pages.ui_helpers import PrimaryButton, SecondaryButton, Card, PageHeader

def buscar_y_botones_component() -> rx.Component:
    return rx.hstack(
        rx.input(
            placeholder="Buscar por nombre, marca",
            on_change=CatalogoState.actualizar_buscar_texto,
            width="300px"
        ),
        PrimaryButton("Buscar", on_click=CatalogoState.buscar),
        SecondaryButton("Ver Carrito", on_click=CatalogoState.ir_a_carrito),
        SecondaryButton("Mis Pedidos", on_click=lambda: rx.redirect("/pedidos")),
        SecondaryButton("Ubicarme", on_click=CatalogoState.ir_a_ubicacion),
        SecondaryButton("Hacer Consulta", on_click=CatalogoState.ir_a_consulta),
        SecondaryButton("Logearse", on_click=CatalogoState.ir_a_login),
        spacing="3",
        justify_content="flex-start",
        margin_bottom="20px"
    )

def producto_card(p: dict) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.box(
                rx.image(
                    src=p.get("imagen", "/static/default.jpg"),
                    alt=p.get("nombre", ""),
                    width="auto",
                    height="100%",
                    border_radius="8px",
                    object_fit="contain",
                ),
                height="160px",
                width="100%",
                display="flex",
                align_items="center",
                justify_content="center",
                overflow="hidden",
                style={"background_color": "#fafafa"}
            ),
            rx.text(
                p.get("nombre", ""),
                font_size="lg",
                font_weight="bold",
                style={"whiteSpace": "nowrap", "overflow": "hidden", "textOverflow": "ellipsis", "width": "100%"}
            ),
            rx.text(f"Talle: {p.get('talle', '')}", font_size="sm"),
            rx.text(f"Precio: ${p.get('precio', '')}", font_size="md"),
            rx.text(f"Marca: {p.get('marca', '')}", font_size="sm"),
            rx.vstack(
                PrimaryButton(
                    "Agregar al Carrito",
                    on_click=lambda _=None, pid=p["id_producto"]: CatalogoState.agregar_carrito_con_id(pid),
                    width="100%",
                ),
                SecondaryButton(
                    "Ver Detalle",
                    on_click=lambda _=None, prod=p: CatalogoState.seleccionar_producto(prod),
                    width="100%",
                ),
                spacing="2",
                width="100%"
            ),
            spacing="2",
            align_items="center",
            justify_content="space-between",
            style={"height": "100%"}
        ),
        border_radius="10px",
        padding="12px",
        margin="10px",
        min_width="200px",
        width="220px",
        height="360px",
        text_align="center",
        box_shadow="0px 2px 5px rgba(0,0,0,0.06)",
        background_color="white",
        border="1px solid #f0f0f0",
    )

def mostrar_productos() -> rx.Component:
    return rx.cond(
        CatalogoState.productos.length() == 0,
        rx.spinner(color="blue", thickness="4px", size="3"),
        rx.hstack(
            rx.foreach(
                CatalogoState.productos.to(list[dict]),
                producto_card
            ),
            flex_wrap="wrap",
            justify_content="center"
        )
    )

@rx.page(route="/catalogo", on_load=CatalogoState.cargar_productos)
def catalogo_page() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.flex(
                PageHeader("Catálogo de Productos", "Encuentra lo que buscas rápidamente."),
                buscar_y_botones_component(),
                rx.cond(
                    CatalogoState.error_message != "",
                    rx.text(CatalogoState.error_message, color="red", margin_bottom="10px"),
                    rx.box()
                ),
                rx.cond(
                    CatalogoState.success_message != "",
                    rx.text(CatalogoState.success_message, color="green", margin_bottom="10px"),
                    rx.box()
                ),
                mostrar_productos(),
                direction="column",
                style={"width": "75%", "padding": "20px"}
            ),
            rx.cond(
                UsersState.logeado,
                rx.card(
                    rx.vstack(
                        rx.heading("👤 Perfil", size="4"),
                        rx.text(f"Nombre: {UsersState.perfil.get('nombre', '')} {UsersState.perfil.get('apellido', '')}"),
                        rx.text(f"Email: {UsersState.perfil.get('email', '')}"),
                        rx.text(f"Teléfono: {UsersState.perfil.get('telefono', '')}"),
                        rx.button("Cerrar sesión", on_click=UsersState.logout)
                    ),
                    width="25%",
                    padding="20px",
                    box_shadow="md",
                    position="sticky",
                    top="20px"
                ),
                rx.box(
                    rx.text("No estás logeado"),
                    width="25%",
                    padding="20px"
                )
            )
        ),
        style={
            "background_color": "#ADD8E6",  # celeste
            "min_height": "100vh",          # ocupa toda la pantalla
            "padding": "20px"
        }
    )