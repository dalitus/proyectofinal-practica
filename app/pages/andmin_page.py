import reflex as rx
from app.service.gerente_service import validar_admin_service
from app.state import app_globals


class AdminLoginState(rx.State):
    error_message: str = ""

    @rx.event
    def validar_admin(self, data: dict):
        try:
            admin = validar_admin_service(
                email=data["email"],
                contrasenia=data["contrasenia"]
            )
            print("Admin logueado:", admin.nombre)
            # 👇 Guardar el id del gerente en la variable global
            app_globals.current_user_id = int(admin.id_gerente)
            return rx.redirect("/admin_dashboard")
        except ValueError as e:
            self.error_message = str(e)


@rx.page(route="/admin_login", title="Login Admin")
def admin_login_page():
    return rx.center(
        rx.vstack(
            rx.heading("Login Admin"),
            rx.form(
                rx.vstack(
                    rx.input(placeholder="Email", name="email"),
                    rx.input(placeholder="Contraseña", name="contrasenia", type_="password"),
                    rx.button("Iniciar sesión", type_="submit"),
                    rx.text(AdminLoginState.error_message, color="red"),
                ),
                on_submit=AdminLoginState.validar_admin,
                reset_on_submit=True,
            ),
        ),
        height="100vh"
    )