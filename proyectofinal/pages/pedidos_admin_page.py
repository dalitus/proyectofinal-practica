# proyectofinal/pages/pedidos_admin_page.py
import reflex as rx
from proyectofinal.state.pedido_state import PedidoState
from proyectofinal.state.data import PedidoAdminData
from proyectofinal.pages.ui_helpers import PageHeader

class PedidosAdminState(rx.State):
    estado_filtro: str = "todos"   # valores: "todos", "en espera", "enviado", "cancelado", "entregado", "reservado"
    producto_filtro: str = ""

    @rx.event
    def set_estado_filtro(self, value: str):
        self.estado_filtro = value


def mostrar_productos(productos) -> rx.Component:
    return rx.cond(
        productos.length() > 0,
        rx.foreach(
            productos,
            lambda prod: rx.hstack(
                rx.text(f"{prod['nombre']} x{prod['cantidad']}", font_size="sm"),
                rx.spacer(),
                rx.text(f"${prod['subtotal']:.2f}", font_size="sm", font_weight="bold"),
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


def pedido_card_admin(pedido) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.text(f"Pedido #{pedido.id_pedido}", font_weight="bold", font_size="1.2em"),
            rx.text(f"Usuario: {pedido.nombre_usuario}"),

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

            rx.hstack(
                rx.button("En Espera", on_click=PedidoState.cambiar_estado_pedido(pedido.id_pedido, "en espera"), color_scheme="orange", size="3"),
                rx.button("Enviado", on_click=PedidoState.cambiar_estado_pedido(pedido.id_pedido, "enviado"), color_scheme="blue", size="3"),
                rx.button("Entregado", on_click=PedidoState.cambiar_estado_pedido(pedido.id_pedido, "entregado"), color_scheme="green", size="3"),
                rx.button("Cancelado", on_click=PedidoState.cambiar_estado_pedido(pedido.id_pedido, "cancelado"), color_scheme="red", size="3"),
                rx.button("Reservado", on_click=PedidoState.cambiar_estado_pedido(pedido.id_pedido, "reservado"), color_scheme="purple", size="3"),
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


def table_pedidos_admin(pedidos: list[PedidoAdminData]) -> rx.Component:
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.cell("ID Pedido", font_weight="bold"),
                rx.table.cell("Usuario", font_weight="bold"),
                rx.table.cell("Fecha", font_weight="bold"),
                rx.table.cell("Total", font_weight="bold"),
                rx.table.cell("Dirección", font_weight="bold"),
                rx.table.cell("Ciudad", font_weight="bold"),
                rx.table.cell("Provincia", font_weight="bold"),
                rx.table.cell("Talles", font_weight="bold"),
                rx.table.cell("Colores", font_weight="bold"),
                rx.table.cell("Estado", font_weight="bold"),
                rx.table.cell("Acciones", font_weight="bold"),
            )
        ),
        rx.table.body(
            rx.foreach(
                pedidos,
                lambda pedido: rx.table.row(
                    rx.table.cell(pedido.id_pedido),
                    rx.table.cell(pedido.nombre_usuario),
                    rx.table.cell(pedido.fecha_pedido),
                    rx.table.cell(f"${pedido.total:.2f}"),
                    rx.table.cell(rx.cond(pedido.direccion != None, pedido.direccion, "N/A")),
                    rx.table.cell(rx.cond(pedido.ciudad != None, pedido.ciudad, "N/A")),
                    rx.table.cell(rx.cond(pedido.provincia != None, pedido.provincia, "N/A")),
                    rx.table.cell(rx.cond(pedido.talles != None, pedido.talles, "N/A")),
                    rx.table.cell(rx.cond(pedido.colores != None, pedido.colores, "N/A")),
                    rx.table.cell(pedido.estado),
                    rx.table.cell(
                        rx.hstack(
                            rx.button("En Espera", on_click=PedidoState.cambiar_estado_pedido(pedido.id_pedido, "en espera"), color_scheme="orange", size="2"),
                            rx.button("Enviado", on_click=PedidoState.cambiar_estado_pedido(pedido.id_pedido, "enviado"), color_scheme="blue", size="2"),
                            rx.button("Entregado", on_click=PedidoState.cambiar_estado_pedido(pedido.id_pedido, "entregado"), color_scheme="green", size="2"),
                            spacing="2"
                        )
                    )
                )
            )
        ),
        width="100%",
        variant="surface",
        size="2",
        margin_y="20px"
    )


def render_pedido_card(p: PedidoAdminData) -> rx.Component:
    return rx.cond(
        (PedidosAdminState.estado_filtro == "todos") | (p.estado == PedidosAdminState.estado_filtro),
        pedido_card_admin(p),
        rx.box()
    )


@rx.page(route="pedidos_admin", title="Pedidos Admin", on_load=PedidoState.get_all_pedidos_admin)
def pedidos_admin_page() -> rx.Component:
    return rx.box(
        rx.flex(
            rx.heading("Pedidos (Admin)", align="center"),

            rx.select(
                ["todos", "en espera", "enviado", "entregado", "cancelado", "reservado"],
                value=PedidosAdminState.estado_filtro,
                on_change=PedidosAdminState.set_estado_filtro,
                placeholder="Filtrar por estado",
                width="200px"
            ),

            rx.cond(
                PedidoState.loading,
                rx.spinner(color="blue"),
                rx.cond(
                    PedidoState.pedidos_admin.length() > 0,
                    rx.vstack(
                        rx.heading("Vista en Tarjetas", size="5"),
                        rx.foreach(PedidoState.pedidos_admin, render_pedido_card),
                        rx.heading("Vista en Tabla", size="5", margin_top="20px"),
                        table_pedidos_admin(PedidoState.pedidos_admin),
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
            "background_color": "#ADD8E6",
            "min_height": "100vh",
            "padding": "20px"
        }
    )