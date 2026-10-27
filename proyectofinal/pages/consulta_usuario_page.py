import reflex as rx
from proyectofinal.ui.tokens import COLORS
from proyectofinal.service.consulta_service import crear_consulta, listar_consultas_usuario
from proyectofinal.state.users_state import UsersState
from proyectofinal.pages.ui_helpers import PrimaryButton, PageHeader


class ConsultaUsuarioState(rx.State):
    asunto: str = ""
    mensaje: str = ""
    usuario_id: int = 1   # ðŸ‘ˆ corregido
    consultas: list[dict] = []
    success_message: str = ""
    error_message: str = ""

    @rx.event
    def on_load(self):
        # Usar el usuario logeado si existe
        try:
            self.usuario_id = UsersState.id or 1   # ðŸ‘ˆ usar el id del usuario logeado
        except Exception:
            self.usuario_id = 1
        self.cargar_consultas()

    @rx.event
    def enviar_consulta(self):
        try:
            if not self.mensaje.strip():
                self.error_message = "El mensaje no puede estar vacÃ­o."
                self.success_message = ""
                return
            crear_consulta(self.usuario_id, self.asunto.strip(), self.mensaje.strip())   # ðŸ‘ˆ corregido
            self.asunto = ""
            self.mensaje = ""
            self.success_message = "Consulta enviada correctamente."
            self.error_message = ""
            self.cargar_consultas()
        except Exception as e:
            self.error_message = f"Error al enviar: {e}"
            self.success_message = ""

    @rx.event
    def cargar_consultas(self):
        consultas_obj = listar_consultas_usuario(self.usuario_id)   # ðŸ‘ˆ corregido
        self.consultas = [c.model_dump() for c in consultas_obj]

    @rx.event
    def actualizar_asunto(self, value: str):
        self.asunto = value

    @rx.event
    def actualizar_mensaje(self, value: str):
        self.mensaje = value


@rx.page(route="/consulta_usuario", title="Consulta Usuario", on_load=ConsultaUsuarioState.on_load)
def consulta_usuario_page() -> rx.Component:
    return rx.box(
        rx.vstack(
            PageHeader("Enviar consulta", "Te responderemos por email lo antes posible."),
            rx.cond(
                ConsultaUsuarioState.success_message != "",
                rx.box(
                    rx.text(ConsultaUsuarioState.success_message),
                    background_color="green.100",
                    padding="8px",
                    border_radius="md"
                ),
                rx.box()
            ),
            rx.cond(
                ConsultaUsuarioState.error_message != "",
                rx.box(
                    rx.text(ConsultaUsuarioState.error_message),
                    background_color="red.100",
                    padding="8px",
                    border_radius="md"
                ),
                rx.box()
            ),
            rx.input(
                placeholder="Asunto",
                value=ConsultaUsuarioState.asunto,
                on_change=ConsultaUsuarioState.actualizar_asunto,
                width="100%",
            ),
            rx.text_area(
                placeholder="Mensaje",
                value=ConsultaUsuarioState.mensaje,
                on_change=ConsultaUsuarioState.actualizar_mensaje,
                width="100%",
            ),
            PrimaryButton("Enviar", on_click=ConsultaUsuarioState.enviar_consulta),
            rx.divider(),
            rx.heading("Tus consultas"),
            # ðŸ‘‡ Usamos rx.foreach directamente, y filtramos en render_consulta_usuario
            rx.foreach(
                ConsultaUsuarioState.consultas,
                render_consulta_usuario
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


def render_consulta_usuario(c: dict) -> rx.Component:
    return rx.cond(
        c["asunto"] == "Compra realizada",
        rx.box(),  # si es automÃ¡tica de compra, no mostramos nada
        rx.box(
            rx.text(f"Asunto: {c.get('asunto', 'Sin asunto')}"),
            rx.text(f"Mensaje: {c.get('mensaje', '')}"),
            rx.cond(
                c.get("respuesta"),
                rx.text(f"Respuesta: {c['respuesta']}"),
                rx.text("Respuesta: Sin respuesta")
            ),
            rx.divider()
        )
    )