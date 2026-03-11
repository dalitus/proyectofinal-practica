# proyectofinal/pages/pedidos_page.py
import reflex as rx
from proyectofinal.state.pedido_state import PedidoState

def mostrar_productos(productos) -> rx.Component:
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
        "entregado": "green",
        "cancelado": "red",
        "reservado": "purple",
    }
    color = color_map.get(estado, "gray")
    return rx.badge(estado.upper(), color_scheme=color, variant="solid")

def pedido_card_usuario(pedido) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.text(f"Pedido #{pedido.id_pedido}", font_weight="bold", font_size="1.2em"),

            rx.cond(pedido.direccion != None, rx.text(f"Calle: {pedido.direccion}"), rx.text("Calle: N/A")),
            rx.cond(pedido.numero != None, rx.text(f"Número: {pedido.numero}"), rx.text("Número: N/A")),
            rx.cond(pedido.departamento != None, rx.text(f"Departamento: {pedido.departamento}"), rx.text("Departamento: N/A")),
            rx.cond(pedido.codigo_postal != None, rx.text(f"Código Postal: {pedido.codigo_postal}"), rx.text("Código Postal: N/A")),
            rx.cond(pedido.ciudad != None, rx.text(f"Ciudad: {pedido.ciudad}"), rx.text("Ciudad: N/A")),
            rx.cond(pedido.provincia != None, rx.text(f"Provincia: {pedido.provincia}"), rx.text("Provincia: N/A")),

            rx.cond(pedido.talles != None, rx.text(f"Talles: {pedido.talles}"), rx.text("Talles: N/A")),
            rx.cond(pedido.colores != None, rx.text(f"Colores: {pedido.colores}"), rx.text("Colores: N/A")),

            rx.text(f"Fecha: {pedido.fecha_pedido}"),
            estado_badge(pedido.estado),

            rx.text("Productos:", font_weight="bold"),
            mostrar_productos(pedido.productos_json),

            rx.text(f"Total: ${pedido.total:.2f}", font_weight="bold"),

            spacing="4",
            align_items="flex-start"
        ),
        width="100%",
        padding="15px",
        margin_y="10px",
        box_shadow="md",
        border_radius="10px"
    )

@rx.page(route="pedidos", title="Mis Pedidos", on_load=PedidoState.cargar_pedidos_usuario)
def pedidos_page() -> rx.Component:
    return rx.box(
        rx.flex(
            rx.heading("Mis Pedidos", align="center"),
            rx.cond(
                PedidoState.loading,
                rx.spinner(color="blue"),
                rx.cond(
                    PedidoState.pedidos_usuario.length() > 0,
                    rx.vstack(
                        rx.foreach(PedidoState.pedidos_usuario, pedido_card_usuario),
                        width="100%",
                        spacing="2"
                    ),
                    rx.text("No tienes pedidos aún", text_align="center", color="gray", margin_top="20px")
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
            "background_color": "#ADD8E6",
            "min_height": "100vh",
            "padding": "20px"
        }
    )