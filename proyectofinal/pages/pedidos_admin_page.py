# proyectofinal/pages/pedidos_admin_page.py
import reflex as rx
from proyectofinal.state.pedido_state import PedidoState

def mostrar_productos(productos: list) -> rx.Component:
    return rx.cond(
        productos.length() > 0,
        rx.foreach(
            productos,
            lambda p: rx.hstack(
                rx.text(f"{p['nombre']} x{p['cantidad']}", font_size="sm"),
                rx.spacer(),
                rx.text(f"${p['subtotal']:.2f}", font_size="sm", font_weight="bold"),
                width="100%",
                spacing="2"
            )
        ),
        rx.text("Sin productos registrados", color="gray", font_size="sm")
    )

def estado_badge(estado: str) -> rx.Component:
    color_map = {
        "en espera": "orange",
        "enviado": "blue",
        "entregado": "green"
    }
    color = color_map.get(estado, "gray")
    return rx.badge(estado.upper(), color_scheme=color, variant="solid")

def pedido_card_admin(pedido) -> rx.Component:
    return rx.card(
        rx.vstack(
            # Encabezado
            rx.text(f"Pedido #{pedido.id_pedido}", font_weight="bold", font_size="1.2em"),
            rx.text(f"Usuario: {pedido.nombre_usuario}"),

            # Dirección completa
            rx.cond(pedido.direccion != None, rx.text(f"Calle: {pedido.direccion}"), rx.text("Calle: N/A")),
            rx.cond(pedido.numero != None, rx.text(f"Número: {pedido.numero}"), rx.text("Número: N/A")),
            rx.cond(pedido.departamento != None, rx.text(f"Departamento: {pedido.departamento}"), rx.text("Departamento: N/A")),
            rx.cond(pedido.codigo_postal != None, rx.text(f"Código Postal: {pedido.codigo_postal}"), rx.text("Código Postal: N/A")),
            rx.cond(pedido.ciudad != None, rx.text(f"Ciudad: {pedido.ciudad}"), rx.text("Ciudad: N/A")),
            rx.cond(pedido.provincia != None, rx.text(f"Provincia: {pedido.provincia}"), rx.text("Provincia: N/A")),

            # Fecha y estado
            rx.text(f"Fecha: {pedido.fecha_pedido}"),
            estado_badge(pedido.estado),

            # Productos
            rx.text("Productos:", font_weight="bold"),
            mostrar_productos(pedido.productos_json),

            # Total
            rx.text(f"Total: ${pedido.total:.2f}", font_weight="bold"),

            # Botones de gestión de estado
            rx.hstack(
                rx.button(
                    "En Espera",
                    on_click=lambda: PedidoState.cambiar_estado_pedido(pedido.id_pedido, "en espera"),
                    color_scheme="orange",
                    size="3"
                ),
                rx.button(
                    "Enviado",
                    on_click=lambda: PedidoState.cambiar_estado_pedido(pedido.id_pedido, "enviado"),
                    color_scheme="blue",
                    size="3"
                ),
                rx.button(
                    "Entregado",
                    on_click=lambda: PedidoState.cambiar_estado_pedido(pedido.id_pedido, "entregado"),
                    color_scheme="green",
                    size="3"
                ),
                spacing="2"
            ),

            spacing="4",
            align_items="flex-start"
        ),
        width="100%",
        padding="15px",
        margin_y="10px",
        box_shadow="md",
        border_radius="10px"
    )

@rx.page(route="pedidos_admin", title="Pedidos Admin", on_load=PedidoState.get_all_pedidos_admin)
def pedidos_admin_page() -> rx.Component:
    return rx.box(
        rx.flex(
            rx.heading("Pedidos (Admin)", align="center"),
            rx.cond(
                PedidoState.loading,
                rx.spinner(color="blue"),
                rx.cond(
                    PedidoState.pedidos.length() > 0,
                    rx.vstack(
                        rx.foreach(PedidoState.pedidos, pedido_card_admin),
                        width="100%",
                        spacing="2"
                    ),
                    rx.text("No hay pedidos registrados", text_align="center", color="gray", margin_top="20px")
                )
            ),
            rx.cond(
                PedidoState.error_message != "",
                rx.box(
                    rx.text(PedidoState.error_message),
                    background_color="red.100",
                    padding="12px",
                    border_radius="8px",
                    color="red.900"
                )
            ),
            direction="column",
            style={"width": "70vw", "margin": "auto", "padding": "20px"},
            spacing="4"
        ),
        style={
            "background_color": "#ADD8E6",  # celeste
            "min_height": "100vh",          # ocupa toda la pantalla
            "padding": "20px"
        }
    )