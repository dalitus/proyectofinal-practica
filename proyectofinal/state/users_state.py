import reflex as rx
import re
from proyectofinal.model.users_model import Users
from proyectofinal.service.users_service import (
    select_all_users_service,
    select_by_email_service,
    select_by_id_service,
    create_user_service,
    delete_user_service,
    validar_usuario_service
)
from proyectofinal.service.gerente_service import validar_admin_service
from proyectofinal.service.notifail import notifail_component

class UsersState(rx.State):
    users: list[Users] = []
    user_buscar: str = ""
    error_message: str = ""
    user_id: int | None = None
    perfil: dict = {}
    logeado: bool = False

    @staticmethod
    async def get_user_id() -> int:
        # Try to safely return an int user id. UsersState.user_id may be a Reflex Var proxy;
        # attempt several access strategies and fall back to 0.
        try:
            uid = UsersState.user_id
            # direct int cast (works if it's already an int)
            return int(uid)
        except Exception:
            try:
                # Var-like with `.get()`
                return int(UsersState.user_id.get())
            except Exception:
                try:
                    # Var-like with `.value`
                    return int(getattr(UsersState.user_id, "value", 0) or 0)
                except Exception:
                    return 0

    @rx.event
    def login(self, usuario_id: int):
        self.user_id = usuario_id
        UsersState.user_id = usuario_id
        self.perfil = select_by_id_service(usuario_id)
        self.logeado = True

        from proyectofinal.state.catalogo_state import CatalogoState
        CatalogoState.user_id = usuario_id
        CatalogoState.cargar_productos()

        from proyectofinal.state.carrito_state import CarritoState
        CarritoState.user_id = usuario_id
        CarritoState.cargar_carrito()

    @rx.event
    def logout(self):
        self.user_id = None
        self.perfil = {}
        self.logeado = False
        return rx.redirect("/users")

    @rx.event
    def validar_usuario(self, data: dict):
        email = data["email"]
        password = data["password"]
        # Primero validar administrador
        try:
            admin = validar_admin_service(email=email, contrasenia=password)
        except Exception:
            admin = None
        if admin:
            self.user_id = admin.id_gerente
            return rx.redirect("/admin_dashboard")

        # Validar usuario regular usando el servicio; capturar errores legibles
        try:
            user = validar_usuario_service(email=email, password=password)
        except Exception as e:
            # servicio levanta ValueError cuando las credenciales son inválidas
            self.error_message = str(e) or "Credenciales inválidas. Intenta nuevamente."
            return notifail_component("Error", self.error_message)

        if user:
            self.login(user.id_users)
            return rx.redirect("/catalogo")

        self.error_message = "Credenciales inválidas. Intenta nuevamente."
        return notifail_component("Error", self.error_message)

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
            # Validaciones básicas por regex
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


