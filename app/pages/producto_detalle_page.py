import reflex as rx
from app.ui.tokens import COLORS
from app.state.catalogo_state import CatalogoState

@rx.page(route="/detalle_producto", title="Detalle Producto")
def detalle_producto_page() -> rx.Component:
    return rx.box(
        rx.center(
            rx.cond(
                CatalogoState.producto_seleccionado.get("id", 0) == 0,
                rx.text("❌ Producto no disponible"),
                rx.card(
                    rx.vstack(
                        rx.image(
                            src=CatalogoState.producto_seleccionado.get("imagen", "/static/default.jpg"),
                            alt=CatalogoState.producto_seleccionado.get("nombre", ""),
                            width="100%",
                            height="360px",
                            border_radius="10px",
                            object_fit="contain",
                            style={"background_color": COLORS["surface"]}
                        ),
                        rx.heading(CatalogoState.producto_seleccionado.get("nombre", ""), size="5"),
                        rx.text(f"Marca: {CatalogoState.producto_seleccionado.get('marca', '')}", font_size="md"),
                        rx.text(f"Precio: ${CatalogoState.producto_seleccionado.get('precio', 0):.2f}", font_size="lg"),
                        rx.text(f"Categoría: {CatalogoState.producto_seleccionado.get('categoria', '')}", font_size="md"),
                        rx.text(f"Talle: {CatalogoState.producto_seleccionado.get('talle', '')}", font_size="md"),
                        rx.text(CatalogoState.producto_seleccionado.get("descripcion", ""), font_size="sm"),
                        rx.button(
                            "🛒 Agregar al Carrito",
                            on_click=lambda _=None, pid=CatalogoState.producto_seleccionado.get("id", 0): CatalogoState.agregar_carrito_con_id(pid)
                        ),
                        rx.button("← Volver al Catálogo", on_click=rx.redirect("/catalogo"))
                    ),
                    padding="30px",
                    background_color=COLORS["card"],
                    border=f"1px solid {COLORS['border']}",
                    border_radius="10px",
                    style={"maxWidth": "900px", "width": "90%"},
                    spacing="4"
                )
            )
        ),
        style={
            "background_color": COLORS["page"],
            "min_height": "100vh",          # ocupa toda la pantalla
            "padding": "20px"
        }
    )