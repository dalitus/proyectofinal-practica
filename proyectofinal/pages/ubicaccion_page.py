import reflex as rx
from proyectofinal.ui.tokens import COLORS

# Estado de ubicación
class UbicacionState(rx.State):
    direccion: str = "Esperanza, Santa Fe, Argentina"
    mensaje: str = ""

    # Guardar dirección
    def guardar_direccion(self):
        self.mensaje = f"Dirección confirmada: {self.direccion}"

# Página de ubicación
@rx.page(route="/ubicacion", title="Ubicación")
def ubicaccion_page() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.heading("Ubicación del Usuario", align="center"),
            rx.image(
                src="https://www.google.com/maps/vt/data=J2ZDs5pMr3OpV4_gw2gOhvAGWh9CjFCaVXpO2WHZ5_htlBnhACkUJgRzVSQvRJIyqf6v20i3MMN6Y9_AAb_tvj5bX0SKTg396_2-g1fVm72SXPlGGnzlQ1EpU-ThGpS53I3L50BqApOEkrVGzPYq4V-r9dSXAia1qlZHXImgH_XWkx-ftp2D",
                alt="Imagen de ubicación",
                width="200px"
            ),
            rx.text(f"📍 Dirección: {UbicacionState.direccion}"),
            rx.cond(
                UbicacionState.mensaje != "",
                rx.text(UbicacionState.mensaje, color="green")
            ),
            spacing="3",
            style={"width": "80vw", "margin": "auto"}
        ),
        style={
            "background_color": COLORS["page"],
            "min_height": "100vh",          # ocupa toda la pantalla
            "padding": "20px"
        }
    )