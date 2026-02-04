import reflex as rx
class UbicacionState(rx.State):
    ubicacion: str = "Esperanza, Santa Fe, Argentina"

    def on_load(self):
        pass  # o cualquier lógica que quieras ejecutar al cargar la página

    
    @rx.page(route="/ubicacion")
    def ubicacion_page():
        return rx.text("Página de ubicación")


@rx.page(route="/ubicacion", on_load=UbicacionState.on_load)
def ubicacion_page():
    return rx.center(
        rx.vstack(
            rx.image(
                src="/reflex_logo.png",  # Asegurate que esté en la carpeta assets/
                alt="Logo Reflex",
                width="100px",
                height="100px"
            ),
            rx.heading("🌍 Ubicación actual", size="3"),
            rx.text(f"📍 Ubicación: {UbicacionState.ubicacion}"),
            rx.text("Esta información se carga desde el estado."),
            spacing="4",
            padding="20px"
        )
    )