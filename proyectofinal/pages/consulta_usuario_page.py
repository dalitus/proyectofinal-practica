import reflex as rx
from proyectofinal.service.consulta_service import crear_consulta, listar_consultas_usuario
from proyectofinal.state.carrito_state import CarritoState
from proyectofinal.state.users_state import UsersState
from proyectofinal.pages.ui_helpers import PrimaryButton, PageHeader

class ConsultaUsuarioState(rx.State):
    asunto: str = ""
    mensaje: str = ""
    id_users: int = 1
    consultas: list[dict] = []
    success_message: str = ""
    error_message: str = ""

    @rx.event
    def on_load(self):
        # Usar el usuario logeado si existe
        try:
            self.id_users = UsersState.user_id or 1
        except Exception:
            self.id_users = 1
        self.cargar_consultas()

    @rx.event
    def enviar_consulta(self):
        try:
            if not self.mensaje.strip():
                self.error_message = "El mensaje no puede estar vacío."
                self.success_message = ""
                return
            crear_consulta(self.id_users, self.asunto.strip(), self.mensaje.strip())
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
        consultas_obj = listar_consultas_usuario(self.id_users)
        self.consultas = [c.dict() for c in consultas_obj]

    @rx.event
    def actualizar_asunto(self, value: str):
        self.asunto = value

    @rx.event
    def actualizar_mensaje(self, value: str):
        self.mensaje = value


@rx.page(route="/consulta_usuario", on_load=ConsultaUsuarioState.on_load)
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
            # 👇 Usamos rx.foreach directamente, y filtramos en render_consulta_usuario
            rx.foreach(
                ConsultaUsuarioState.consultas,
                render_consulta_usuario
            ),
            spacing="3",
            style={"width": "80vw", "margin": "auto"}
        ),
        style={
            "background_color": "#ADD8E6",  # celeste
            "min_height": "100vh",          # ocupa toda la pantalla
            "padding": "20px"
        }
    )


def render_consulta_usuario(c: dict) -> rx.Component:
    return rx.cond(
        c["asunto"] == "Compra realizada",
        rx.box(),  # si es automática de compra, no mostramos nada
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