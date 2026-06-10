import reflex as rx
import re
from proyectofinal.state import app_globals
from proyectofinal.model.users_model import Users
from proyectofinal.service.users_service import (
    select_all_users_service,
    select_by_email_service,
    select_by_id_service,
    create_user_service,
    delete_user_service,
    validar_usuario_service,
)
from proyectofinal.service.gerente_service import validar_admin_service
from proyectofinal.service.notifail import notifail_component


class UsersState(rx.State):
    users: list[Users] = []
    user_buscar: str = ""
    error_message: str = ""
    perfil: dict = {}
    logeado: bool = False

    id: int | None = None        # reactivo
    id_value: int | None = None  # 👈 declarar aquí el valor crudo


    @rx.event
    def set_perfil(self, perfil: dict):
        self.perfil = perfil
        self.logeado = True
        app_globals.current_user_id = int(perfil.get("id")) if perfil and perfil.get("id") else None
        self.id = app_globals.current_user_id

    @rx.event
    def login(self, usuario_id: int):
        user = select_by_id_service(usuario_id)
        if isinstance(user, Users):
            self.perfil = user.dict()
        elif isinstance(user, dict):
            self.perfil = user
        else:
            self.perfil = {"id": usuario_id}
        self.logeado = True
        app_globals.current_user_id = int(self.perfil.get("id")) if self.perfil.get("id") else None
        self.id = app_globals.current_user_id
        print("Perfil guardado:", self.perfil)

    @rx.event
    def logout(self):
        self.perfil = {}
        self.logeado = False
        app_globals.current_user_id = None
        self.id = None
        return rx.redirect("/users")

    @rx.event
    def validar_usuario(self, data: dict):
        email = data["email"]
        password = data["password"]

        # Validar administrador
        try:
            admin = validar_admin_service(email=email, contrasenia=password)
        except Exception:
            admin = None
        if admin:
            self.perfil = {"id": admin.id_gerente}
            self.logeado = True
            self.id_value = int(admin.id_gerente)
            self.id = self.id_value
            app_globals.current_user_id = self.id_value   # 👈 actualizar global
            return rx.redirect("/admin_dashboard")

        # Validar usuario regular
        try:
            user = validar_usuario_service(email=email, password=password)
        except Exception as e:
            self.error_message = str(e) or "Credenciales inválidas. Intenta nuevamente."
            return notifail_component(self.error_message, "red")

        if user:
            if isinstance(user, Users):
                self.perfil = user.dict()
            elif isinstance(user, dict):
                self.perfil = user
            else:
                self.perfil = {"id": getattr(user, "id", None)}
            self.logeado = True
            self.id_value = int(self.perfil.get("id")) if self.perfil.get("id") else None
            self.id = self.id_value
            app_globals.current_user_id = self.id_value   # 👈 actualizar global
            print("Perfil guardado:", self.perfil)
            return rx.redirect("/catalogo")

        self.error_message = "Credenciales inválidas. Intenta nuevamente."
        return notifail_component(self.error_message, "red")

    @rx.event
    def buscar_on_change(self, value: str):
        self.user_buscar = value

    @rx.event
    def get_user_by_email(self):
        self.users = select_by_email_service(self.user_buscar)

    @rx.event
    def get_all_users(self):
        self.users = select_all_users_service()

    @rx.event
    def create_user(self, data: dict):
        try:
            name_pat = re.compile(r'^[A-Za-zÁÉÍÓÚáéíóúÑñÜü\s\-]{1,80}$')
            email_pat = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
            phone_pat = re.compile(r'^[0-9\s\+\-()]{6,20}$')
            pwd = (data.get("contrasena") or "").strip()

            if not data.get("nombre") or not name_pat.match(data.get("nombre")):
                self.error_message = "Nombre inválido"
                return
            if not data.get("apellido") or not name_pat.match(data.get("apellido")):
                self.error_message = "Apellido inválido"
                return
            if not data.get("email") or not email_pat.match(data.get("email")):
                self.error_message = "Email inválido"
                return
            if data.get("telefono") and not phone_pat.match(data.get("telefono")):
                self.error_message = "Teléfono inválido"
                return
            if not pwd or len(pwd) < 6:
                self.error_message = "La contraseña debe tener al menos 6 caracteres"
                return

            create_user_service(**data)
            self.users = select_all_users_service()
            self.error_message = ""
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error_message = f"Error al crear usuario: {e}"

    @rx.event
    def delete_user(self, email: str):
        delete_user_service(email)
        self.users = select_all_users_service()