import reflex as rx
from app.ui.tokens import COLORS
from app.state.users_state import UsersState
from app.service.notifail import notifail_component
from app.model.users_model import Users

@rx.page(route="users", title="Users", on_load=UsersState.get_all_users)
def users_page() -> rx.Component:
    return rx.box(
        rx.flex(
            rx.heading("Usuarios", align="center"),
            # Botones centrados
            rx.hstack(
                create_user_dialogo_component(),
                validar_usuario_button(),
                justify="center",   # centra los botones
                width="100%",       # ocupa todo el ancho
                spacing="4"
            ),
            # 👇 Título debajo de los botones
            rx.heading(
                "Calzado Fermín",
                font_style="cursive",   # cursiva
                size="9",              # mucho más grande (≈ 5 veces el texto normal)
                text_align="center",
                width="100%",          # ocupa toda la pantalla en ancho
                margin_top="40px"
            ),
            rx.cond(
                UsersState.error_message != "",
                notifail_component(
                    mensaje=UsersState.error_message,
                    icon_notify="shield_alert",
                    color="red"
                )
            ),
            direction="column",
            style={"width": "60vw", "margin": "auto"},
        ),
        style={
            "background_color": COLORS["page"],
            "min_height": "100vh",          # ocupa toda la pantalla
            "padding": "20px"
        }
    )

def table_users(list_user: list[Users]) -> rx.Component:
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.column_header_cell("Nombre"),
                rx.table.column_header_cell("Apellido"),
                rx.table.column_header_cell("Email"),
                rx.table.column_header_cell("Teléfono"),
                rx.table.column_header_cell("Acciones"),
            )
        ),
        
    )



def buscar_user_component() -> rx.Component:
    return rx.hstack(
        rx.input(
            placeholder="Buscar por email",
            on_change=UsersState.buscar_on_change
        ),
        rx.button("Buscar usuario", on_click=UsersState.get_user_by_email)
    )

def create_user_form() -> rx.Component:
    return rx.form(
        rx.vstack(
            rx.text("Nombre", font_weight="bold"),
            rx.input(name="nombre", width="100%"),
            
            rx.text("Apellido", font_weight="bold"),
            rx.input(name="apellido", width="100%"),
            
            rx.text("Email", font_weight="bold"),
            rx.input(name="email", width="100%"),
            
            rx.text("Teléfono", font_weight="bold"),
            rx.input(name="telefono", width="100%"),
            
            rx.text("Contraseña", font_weight="bold"),
            rx.input(name="contrasena", type="password", width="100%"),
            
            rx.dialog.close(
                rx.button("Guardar", type="submit", width="100%")
            ),
            spacing="4",
            width="100%"
        ),
        on_submit=UsersState.create_user,
    )

def create_user_dialogo_component() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.trigger(rx.button("Crear Usuario")),
        rx.dialog.content(
            rx.flex(
                rx.dialog.title("Crear Usuario"),
                create_user_form(),
                justify="center",
                align="center",
                direction="column",
            ),
            rx.flex(
                rx.dialog.close(
                    rx.button("Cancelar", variant="soft", color_scheme="gray")
                ),
                spacing="3",
                margin_top="16px",
                justify="center",
            ),
            style={"width": "400px"}
        ),
    )

def delete_user_button(email: str) -> rx.Component:
    return rx.dialog.root(
        rx.dialog.trigger(rx.button(rx.icon("trash-2"))),
        rx.dialog.content(
            rx.dialog.title("Confirmación"),
            rx.dialog.description(f"¿Estás seguro de que deseas eliminar el usuario con email: {email}?"),
            rx.flex(
                rx.dialog.close(
                    rx.button("Cancelar", variant="soft", color_scheme="gray")
                ),
                rx.dialog.close(
                    rx.button("Confirmar", on_click=UsersState.delete_user(email))
                ),
                spacing="3",
                margin_top="16px",
                justify="center",
            ),
            style={"width": "350px"},
        )
    )

def validar_usuario_button() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.trigger(rx.button("Iniciar Sesión")),
        rx.dialog.content(
            rx.form(
                rx.vstack(
                    rx.dialog.title("Iniciar Sesión"),
                    
                    # Etiqueta arriba del campo Email
                    rx.text("Email", font_weight="bold"),
                    rx.input(name="email", width="100%"),
                    
                    # Etiqueta arriba del campo Contraseña
                    rx.text("Contraseña", font_weight="bold", margin_top="10px"),
                    rx.input(name="password", type="password", width="100%"),
                    
                    rx.dialog.close(
                        rx.button("Iniciar Sesión", type="submit", width="100%")
                    ),
                    spacing="4",
                    width="100%"
                ),
                on_submit=UsersState.validar_usuario
            ),
            style={"width": "400px", "padding": "20px", "border_radius": "8px"}
        ),
    )
