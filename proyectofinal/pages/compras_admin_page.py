import reflex as rx
from proyectofinal.service.consulta_service import listar_todas_consultas
from proyectofinal.service.pedido_service import obtener_todos_pedidos
from pydantic import BaseModel
import json

class PedidoAdminData(BaseModel):
    id_pedido: int
    id_users: int
    nombre_usuario: str
    estado: str
    total: float
    fecha_pedido: str
    fecha_entrega: str | None = None
    productos_json: str = ""
    direccion: str | None = None
    numero: str | None = None
    departamento: str | None = None
    codigo_postal: str | None = None
    ciudad: str | None = None
    provincia: str | None = None

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

def mostrar_productos_admin(productos_json: str) -> rx.Component:
    """Mostrar los productos del pedido"""
    try:
        if not productos_json or productos_json == "None" or productos_json == "[]":
            return rx.text("Sin productos", color="gray", font_size="sm")
        
        productos = json.loads(productos_json)
        
        if not productos or len(productos) == 0:
            return rx.text("Sin productos", color="gray", font_size="sm")
        
        items_html = ""
        for p in productos:
            nombre = p.get('nombre', 'Producto')
            cantidad = p.get('cantidad', 1)
            subtotal = p.get('subtotal', 0)
            items_html += f"<li>{nombre} x{cantidad} - ${subtotal:.2f}</li>"
        
        return rx.html(f"<ul style='margin: 0; padding-left: 20px;'>{items_html}</ul>")
    except:
        return rx.text("Error al mostrar productos", color="gray", font_size="sm")

def mostrar_ubicacion_admin(pedido: PedidoAdminData) -> rx.Component:
    """Mostrar los datos de ubicación del pedido"""
    direccion_partes = []
    if pedido.direccion:
        direccion_partes.append(pedido.direccion)
    if pedido.numero:
        direccion_partes.append(f"Nº {pedido.numero}")
    if pedido.departamento:
        direccion_partes.append(pedido.departamento)
    
    direccion_completa = ", ".join(direccion_partes) if direccion_partes else "N/A"
    
    ubicacion_partes = []
    if pedido.codigo_postal:
        ubicacion_partes.append(pedido.codigo_postal)
    if pedido.ciudad:
        ubicacion_partes.append(pedido.ciudad)
    if pedido.provincia:
        ubicacion_partes.append(pedido.provincia)
    
    ubicacion_completa = ", ".join(ubicacion_partes) if ubicacion_partes else ""
    
    return rx.vstack(
        rx.text(f"📍 {direccion_completa}", font_size="sm"),
        rx.cond(
            ubicacion_completa != "",
            rx.text(ubicacion_completa, font_size="xs", color="gray"),
            rx.box()
        ),
        spacing="0",
        width="100%"
    )

def pedido_admin_card(pedido: PedidoAdminData) -> rx.Component:
    """Tarjeta para mostrar un pedido en la vista admin"""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.vstack(
                    rx.text(
                        f"Pedido #{pedido.id_pedido}",
                        font_weight="bold",
                        font_size="md"
                    ),
                    rx.text(
                        f"Usuario: {pedido.nombre_usuario} (ID: {pedido.id_users})",
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
            rx.hstack(
                rx.vstack(
                    rx.text("📦 Productos:", font_weight="bold", font_size="sm"),
                    mostrar_productos_admin(pedido.productos_json),
                    spacing="1",
                    width="100%"
                ),
                rx.vstack(
                    rx.text("🚚 Entrega:", font_weight="bold", font_size="sm"),
                    mostrar_ubicacion_admin(pedido),
                    spacing="1",
                    width="100%"
                ),
                spacing="4",
                width="100%"
            ),
            rx.hstack(
                rx.text("Total:", font_weight="bold"),
                rx.text(f"${pedido.total:.2f}", font_size="lg", color="green", font_weight="bold"),
                rx.spacer(),
                rx.cond(
                    (pedido.fecha_entrega is not None) & (pedido.fecha_entrega != ""),
                    rx.text(f"Entregado: {pedido.fecha_entrega}", font_size="xs", color="green"),
                    rx.box()
                ),
                width="100%"
            ),
            spacing="3",
            width="100%"
        ),
        padding="16px",
        margin_bottom="12px",
        border_radius="8px",
        border="1px solid #e0e0e0",
        background_color="white",
        box_shadow="0px 1px 3px rgba(0,0,0,0.1)",
        width="100%"
    )

@rx.page(route="/compras_admin")
def compras_admin_page() -> rx.Component:
    # Obtener todos los pedidos con datos de ubicación
    pedidos_data = obtener_todos_pedidos()
    pedidos = [PedidoAdminData(**p) for p in pedidos_data]
    
    return rx.vstack(
        rx.heading("📦 Gestión de Pedidos (Admin)"),
        rx.divider(),
        rx.cond(
            len(pedidos) > 0,
            rx.vstack(
                rx.text(
                    f"Total de pedidos: {len(pedidos)}",
                    font_size="sm",
                    color="gray"
                ),
                rx.vstack(
                    [pedido_admin_card(p) for p in pedidos],
                    spacing="2",
                    width="100%"
                ),
                spacing="4",
                width="100%"
            ),
            rx.text(
                "No hay pedidos registrados",
                text_align="center",
                color="gray",
                padding="20px"
            )
        ),
        style={"padding": "20px", "max_width": "1000px", "margin": "auto"},
        spacing="4",
        width="100%"    )