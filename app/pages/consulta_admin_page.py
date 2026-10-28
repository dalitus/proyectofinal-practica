import reflex as rx
from app.ui.tokens import COLORS
from app.service.consulta_service import (
    responder_consulta,
    listar_todas_consultas,
    eliminar_consulta,
)
from app.pages.ui_helpers import PageHeader, PrimaryButton, SecondaryButton, DangerButton

class ConsultaAdminState(rx.State):
    consultas: list[dict] = []
    respuesta: str = ""
    consulta_seleccionada: dict | None = None

    estado_filtro: str = "todos"   # valores: "todos", "pendiente", "respondida"

    @rx.event
    def set_estado_filtro(self, value: str):
        self.estado_filtro = value

    @rx.event
    def cargar_consultas(self):
        # Obtener todas las consultas desde el servicio y convertir a dicts
        consultas = [c.model_dump() for c in listar_todas_consultas()]
        # Ordenar: pendientes primero, respondidas al final (asÃ­ al responder quedan abajo)
        consultas.sort(key=lambda x: bool(x.get("respuesta")))
        self.consultas = consultas

    @rx.event
    def seleccionar_consulta(self, consulta_id: int):
        self.consulta_seleccionada = next(
            (c for c in self.consultas if c["id_consulta"] == consulta_id), None
        )
        self.respuesta = ""
        # Si se seleccionÃ³ una consulta vÃ¡lida, navegar al ancla del formulario
        try:
            if consulta_id and int(consulta_id) > 0:
                return rx.redirect("/consulta_admin#responder")
        except Exception:
            pass

    @rx.event
    def enviar_respuesta(self):
        if self.consulta_seleccionada and self.respuesta.strip():
            responder_consulta(self.consulta_seleccionada["id_consulta"], self.respuesta.strip())
            self.consulta_seleccionada = None
            self.respuesta = ""
            self.cargar_consultas()

    @rx.event
    def set_respuesta(self, value: str):
        self.respuesta = value

    @rx.event
    def eliminar_consulta(self, consulta_id: int):
        eliminar_consulta(consulta_id)
        self.cargar_consultas()

def mostrar_consultas_admin_component():
    return rx.vstack(
        rx.foreach(
            ConsultaAdminState.consultas,
            lambda c: rx.cond(
                (
                    (ConsultaAdminState.estado_filtro == "todos")
                    | ((ConsultaAdminState.estado_filtro == "respondida") & (c.get("respuesta") != None))
                    | ((ConsultaAdminState.estado_filtro == "pendiente") & (c.get("respuesta") == None))
                ),
                render_consulta_card(c),
                rx.box()
            )
        ),
        spacing="4",
    )

def render_consulta_card(c: dict) -> rx.Component:
    # ðŸ‘‡ Usamos rx.cond para ocultar las consultas automÃ¡ticas de compra
    return rx.cond(
        c["asunto"] == "Compra realizada",
        rx.box(),  # no mostramos nada si es una consulta de compra
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.vstack(
                        rx.text(f"ðŸ§‘ Usuario ID: {c.get('id_users', '')}", font_weight="bold"),
                        rx.text(f"ðŸ“Œ Asunto: {c.get('asunto', 'Sin asunto')}")
                    ),
                    rx.spacer(),
                    rx.vstack(
                        rx.text(f"ðŸ“… {c.get('fecha_creacion', 'Desconocida')}", font_size="sm"),
                        rx.hstack(
                            rx.cond(
                                c.get("respuesta"),
                                rx.badge("Respondida", color_scheme="green"),
                                rx.badge("Pendiente", color_scheme="yellow")
                            ),
                            DangerButton(
                                "ðŸ—‘ï¸",
                                on_click=lambda _=None, cid=c.get("id_consulta"): ConsultaAdminState.eliminar_consulta(cid),
                                variant="ghost"
                            ),
                            rx.cond(
                                c.get("respuesta") == None,
                                SecondaryButton(
                                    "âœï¸ Responder",
                                    on_click=lambda _=None, cid=c.get("id_consulta"): ConsultaAdminState.seleccionar_consulta(cid),
                                    color_scheme="blue"
                                ),
                                rx.box()
                            )
                        )
                    )
                ),
                rx.box(rx.text(c.get('mensaje', ''), style={"whiteSpace": "pre-wrap"})),
                rx.cond(
                    c.get('respuesta'),
                    rx.box(
                        rx.text(f"âœ… Respuesta: {c.get('respuesta', '')}"),
                        background_color="gray.50",
                        padding="8px",
                        border_radius="6px"
                    ),
                    rx.box()
                ),
                spacing="3"
            ),
            padding="10px",
            margin_y="6px",
            background_color=COLORS["card"],
            border=f"1px solid {COLORS['border']}"
        )
    )

@rx.page(route="/consulta_admin", title="Consulta Admin", on_load=ConsultaAdminState.cargar_consultas)
def consulta_admin_page() -> rx.Component:
    return rx.box(
        rx.container(
            rx.vstack(
                PageHeader("ðŸ“¬ Consultas de usuarios", "RevisÃ¡ y respondÃ© las consultas recibidas"),
                rx.hstack(
                    rx.select(
                        ["todos", "pendiente", "respondida"],
                        value=ConsultaAdminState.estado_filtro,
                        on_change=ConsultaAdminState.set_estado_filtro,
                        placeholder="Filtrar por estado",
                        width="200px"
                    ),
                    margin_bottom="20px"
                ),
                mostrar_consultas_admin_component(),
                rx.cond(
                    ConsultaAdminState.consulta_seleccionada is not None,
                    rx.box(
                        rx.heading("âœï¸ Responder consulta", size="3"),
                        rx.text(f"Asunto: {ConsultaAdminState.consulta_seleccionada['asunto']}"),
                        rx.text(f"Mensaje: {ConsultaAdminState.consulta_seleccionada['mensaje']}"),
                        rx.text_area(
                            placeholder="EscribÃ­ tu respuesta...",
                            value=ConsultaAdminState.respuesta,
                            on_change=ConsultaAdminState.set_respuesta,
                            width="100%",
                            height="120px",
                            margin_top="10px"
                        ),
                        rx.hstack(
                            PrimaryButton("Enviar respuesta", on_click=ConsultaAdminState.enviar_respuesta),
                            SecondaryButton("Cancelar", on_click=lambda _=None: ConsultaAdminState.seleccionar_consulta(0))
                        ),
                        id="responder",
                        border="1px solid #888",
                        border_radius="8px",
                        padding="10px",
                        margin_top="20px"
                    )
                )
            ),
            padding="20px"
        ),
        style={
            "background_color": COLORS["page"],
            "min_height": "100vh",
            "padding": "20px"
        }
    )