import reflex as rx
from proyectofinal.state.pedido_state import PedidoState
from proyectofinal.pages.ui_helpers import PrimaryButton, SecondaryButton, DangerButton
from pydantic import BaseModel
import json

class PedidoData(BaseModel):
    id_pedido: int
    id_users: int
    estado: str
    total: float
    fecha_pedido: str
    fecha_entrega: str | None = None
    nombre_usuario: str = "N/A"
    direccion: str = "N/A"
    productos_json: str = ""

def mostrar_productos(productos_json: str) -> rx.Component:
    """Mostrar los productos del pedido"""
    try:
        # Manejar None y strings vacíos
        if not productos_json or productos_json == "None" or productos_json == "[]":
            return rx.text("Sin productos registrados", color="gray", font_size="sm")
        
        # Parsear JSON
        productos = json.loads(productos_json)
        
        if not productos or len(productos) == 0:
            return rx.text("Sin productos registrados", color="gray", font_size="sm")
        
        # Convertir a formato que Reflex pueda procesar
        items_html = ""
        for p in productos:
            nombre = p.get('nombre', 'Producto')
            cantidad = p.get('cantidad', 1)
            subtotal = p.get('subtotal', 0)
            items_html += f"<div style='padding: 8px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between;'><span>{nombre} x{cantidad}</span><strong>${subtotal:.2f}</strong></div>"
        
        if items_html:
            return rx.html(items_html)
        else:
            return rx.text("Sin información de productos", color="gray", font_size="sm")
    except Exception as e:
        # Si hay error al parsear, intenta obtener del carrito
        return rx.text("Sin información de productos", color="gray", font_size="sm")

def estado_badge(estado: str) -> rx.Component:
    """Componente visual para mostrar el estado del pedido"""
    color_map = {
        "en espera": "orange",
        "enviado": "blue",
        "entregado": "green"
    }
    color = color_map.get(estado, "gray")
    
    return rx.badge(
        estado.upper(),
        color_scheme=color,
        variant="solid"
    )

def cambiar_estado_dialog(id_pedido: int) -> rx.Component:
    """Dialog para cambiar el estado del pedido"""
    return rx.dialog.root(
        rx.dialog.trigger(PrimaryButton("Cambiar Estado", width="100%")),
        rx.dialog.content(
            rx.flex(
                rx.dialog.title("Cambiar Estado del Pedido"),
                rx.vstack(
                    PrimaryButton(
                        "En Espera",
                        on_click=lambda: PedidoState.cambiar_estado_pedido(id_pedido, "en espera"),
                        width="100%"
                    ),
                    PrimaryButton(
                        "Enviado",
                        on_click=lambda: PedidoState.cambiar_estado_pedido(id_pedido, "enviado"),
                        width="100%"
                    ),
                    PrimaryButton(
                        "Entregado",
                        on_click=lambda: PedidoState.cambiar_estado_pedido(id_pedido, "entregado"),
                        width="100%"
                    ),
                    spacing="2",
                    width="100%"
                ),
                rx.flex(
                    rx.dialog.close(
                        rx.button("Cerrar", variant="soft", color_scheme="gray")
                    ),
                    spacing="3",
                    margin_top="16px",
                    justify="center",
                ),
                direction="column",
                spacing="3",
            ),
            style={"width": "350px"}
        ),
    )

def pedido_card_admin(pedido: PedidoData) -> rx.Component:
    """Tarjeta para gestionar un pedido (admin)"""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.vstack(
                    rx.text(
                        f"Pedido #{pedido.id_pedido}",
                        font_weight="bold",
                        font_size="lg"
                    ),
                    rx.text(
                        f"Usuario: {pedido.nombre_usuario}",
                        font_size="sm",
                        color="gray"
                    ),
                    rx.text(
                        f"Dirección: {pedido.direccion}",
                        font_size="sm",
                        color="gray"
                    ),
                    rx.text(
                        f"Fecha: {pedido.fecha_pedido}",
                        font_size="sm",
                        color="gray"
                    ),
                    spacing="1"
                ),
                estado_badge(pedido.estado),
                justify_content="space-between",
                align_items="flex-start",
                width="100%"
            ),
            rx.divider(),
            rx.vstack(
                rx.text("Productos:", font_weight="bold", font_size="md"),
                mostrar_productos(pedido.productos_json),
                spacing="2",
                width="100%"
            ),
            rx.divider(),
            rx.hstack(
                rx.vstack(
                    rx.text("Total:", font_weight="bold"),
                    rx.text(f"${pedido.total:.2f}", font_size="xl", color="green"),
                    spacing="1"
                ),
                rx.cond(
                    (pedido.fecha_entrega is not None) & (pedido.fecha_entrega != ""),
                    rx.vstack(
                        rx.text("Entregado:", font_weight="bold"),
                        rx.text(f"{pedido.fecha_entrega}", font_size="sm", color="green"),
                        spacing="1"
                    ),
                    rx.spacer()
                ),
                justify_content="space-between",
                width="100%"
            ),
            rx.divider(),
            cambiar_estado_dialog(pedido.id_pedido),
            spacing="3",
            width="100%"
        ),
        padding="16px",
        margin_bottom="12px",
        border_radius="8px",
        border="1px solid #e0e0e0",
        background_color="white",
        box_shadow="0px 1px 3px rgba(0,0,0,0.05)",
        width="100%"
    )

@rx.page(route="pedidos_admin", title="Gestión de Pedidos", on_load=PedidoState.get_all_pedidos_admin)
def pedidos_admin_page() -> rx.Component:
    return rx.flex(
        rx.heading("Gestión de Pedidos (Admin)", align="center"),
        rx.cond(
            PedidoState.loading,
            rx.spinner(color="blue"),
            rx.cond(
                PedidoState.pedidos.length() > 0,
                rx.vstack(
                    rx.foreach(
                        PedidoState.pedidos.to(list[PedidoData]),
                        pedido_card_admin
                    ),
                    width="100%",
                    spacing="2"
                ),
                rx.text(
                    "No hay pedidos para gestionar",
                    text_align="center",
                    color="gray",
                    margin_top="20px"
                )
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
        rx.cond(
            PedidoState.success_message != "",
            rx.box(
                rx.text(PedidoState.success_message),
                background_color="green.100",
                padding="12px",
                border_radius="8px",
                color="green.900"
            )
        ),
        direction="column",
        style={"width": "80vw", "margin": "auto", "padding": "20px"},
        spacing="4"
    )
