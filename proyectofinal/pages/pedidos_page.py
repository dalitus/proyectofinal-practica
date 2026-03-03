# proyectofinal/pages/pedidos_page.py
import reflex as rx
import json
from proyectofinal.state.data import PedidoData
from proyectofinal.state.pedido_state import PedidoState

def mostrar_productos(productos_json: str) -> rx.Component:
    try:
        if not productos_json or productos_json in ["None", "[]"]:
            return rx.text("Sin productos registrados", color="gray", font_size="sm")
        
        productos = json.loads(productos_json)
        if not productos:
            return rx.text("Sin productos registrados", color="gray", font_size="sm")
        
        return rx.table(
            rx.thead(
                rx.tr(
                    rx.th("Producto"),
                    rx.th("Cantidad"),
                    rx.th("Subtotal")
                )
            ),
            rx.tbody(
                *[
                    rx.tr(
                        rx.td(p.get("nombre", "Producto")),
                        rx.td(str(p.get("cantidad", 1))),
                        rx.td(f"${p.get('subtotal', 0):.2f}")
                    )
                    for p in productos
                ]
            ),
            width="100%",
            border="1px solid #ccc",
            border_collapse="collapse",
            margin_top="10px"
        )
    except Exception:
        return rx.text("Sin información de productos", color="gray", font_size="sm")

def estado_badge(estado: str) -> rx.Component:
    color_map = {
        "en espera": "orange",
        "enviado": "blue",
        "entregado": "green"
    }
    color = color_map.get(estado, "gray")
    return rx.badge(estado.upper(), color_scheme=color, variant="solid")

def pedido_card(pedido: PedidoData) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.text(f"Pedido #{pedido.id_pedido}", font_weight="bold", font_size="1.2em"),
            rx.text(f"Fecha: {pedido.fecha_pedido}"),
            estado_badge(pedido.estado),
            rx.text(f"Total: ${pedido.total:.2f}", font_weight="bold"),
            mostrar_productos(pedido.productos_json),
            spacing="4",
            align_items="flex-start"
        ),
        width="100%",
        padding="15px",
        margin_y="10px",
        box_shadow="md",
        border_radius="10px"
    )

# 🔹 Usamos un wrapper para resetear y cargar pedidos al entrar en la página
@rx.page(route="pedidos", title="Mis Pedidos", on_load=lambda: PedidoState.reset_and_load())
def pedidos_page() -> rx.Component:
    return rx.flex(
        rx.heading("Mis Pedidos", align="center"),
        rx.cond(
            PedidoState.loading,
            rx.spinner(color="blue"),
            rx.cond(
                PedidoState.pedidos.length() > 0,
                rx.vstack(
                    rx.foreach(PedidoState.pedidos, pedido_card),
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
        style={"width": "60vw", "margin": "auto", "padding": "20px"},
        spacing="4"
    )