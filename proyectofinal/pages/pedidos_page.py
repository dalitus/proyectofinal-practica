import reflex as rx
from proyectofinal.state.pedido_state import PedidoState
from proyectofinal.pages.ui_helpers import SecondaryButton
from pydantic import BaseModel
import json
from proyectofinal.state.pedido_state import PedidoState
from proyectofinal.model.pedido_model import Pedido


class Pedido(BaseModel):
    id_pedido: int
    estado: str
    total: float
    fecha_pedido: str
    fecha_entrega: str | None = None
    nombre_usuario: str = "Mi Pedido"
    direccion: str = ""
    numero: str | None = None
    departamento: str | None = None
    codigo_postal: str | None = None
    ciudad: str | None = None
    provincia: str | None = None
    productos_json: str = ""

def mostrar_producto_item(producto: dict) -> rx.Component:
    """Mostrar un producto individual"""
    return rx.box(
        rx.hstack(
            rx.text(
                f"{producto.get('nombre', 'Producto')} x{producto.get('cantidad', 1)}",
                font_size="sm"
            ),
            rx.spacer(),
            rx.text(
                f"${producto.get('subtotal', 0):.2f}",
                font_size="sm",
                font_weight="bold"
            ),
            width="100%"
        ),
        padding="8px",
        border_bottom="1px solid #eee"
    )

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




def mostrar_ubicacion(pedido: Pedido) -> rx.Component:
    # Usamos rx.cond en lugar de if
    return rx.cond(
        pedido.direccion != "",
        rx.text(f"Dirección: {pedido.direccion}"),
        rx.text("Sin dirección")
    )


def pedido_card(pedido: Pedido) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.text(f"Pedido #{pedido.id_pedido}", font_weight="bold", font_size="1.2em"),
            rx.text(f"Fecha: {pedido.fecha_pedido}"),
            rx.text(f"Estado: {pedido.estado}"),
            mostrar_ubicacion(pedido),
            spacing="4",
            align_items="flex-start"
        ),
        width="100%",
        padding="15px",
        margin_y="10px",
        box_shadow="md",
        border_radius="10px"
    )

@rx.page(route="pedidos", title="Mis Pedidos", on_load=PedidoState.get_all_pedidos)
def pedidos_page() -> rx.Component:
    return rx.flex(
        rx.heading("Mis Pedidos", align="center"),
        rx.cond(
            PedidoState.loading,
            rx.spinner(color="blue"),
            rx.cond(
                PedidoState.pedidos.length() > 0,
                rx.vstack(
                    rx.foreach(
                        PedidoState.pedidos.to(list[Pedido]),
                        pedido_card
                    ),
                    width="100%",
                    spacing="2"
                ),
                rx.text(
                    "No tienes pedidos aún",
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
        direction="column",
        style={"width": "60vw", "margin": "auto", "padding": "20px"},
        spacing="4"
    )
