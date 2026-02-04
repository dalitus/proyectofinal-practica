import reflex as rx
from proyectofinal.service.catalogo_service import (
    obtener_catalogo,
    buscar_en_catalogo
)
from proyectofinal.service.carrito_service import agregar_producto_service
from proyectofinal.state.users_state import UsersState

class CatalogoState(rx.State):
    productos: list[dict] = []
    producto_seleccionado: dict = {}
    buscar_texto: str = ""
    error_message: str = ""
    success_message: str = ""
    user_id: int | None = None

    @rx.event
    def seleccionar_producto(self, producto: dict):
        self.producto_seleccionado = producto
        return rx.redirect(f"/detalle_producto/{producto['id_producto']}")

    @rx.event
    def cargar_productos(self):
        self.productos = obtener_catalogo()
        self.error_message = ""
        self.success_message = ""

    @rx.event
    def actualizar_buscar_texto(self, value: str):
        self.buscar_texto = value

    @rx.event
    def buscar(self):
        resultados = buscar_en_catalogo(self.buscar_texto)
        if resultados:
            self.productos = resultados
            self.error_message = ""
        else:
            self.productos = []
            # Silenciar el mensaje para búsquedas sin resultados
            self.error_message = ""

    @rx.event
    async def agregar_carrito_con_id(self, producto_id: int):
        # Validar id de producto
        try:
            if not producto_id or int(producto_id) <= 0:
                self.error_message = "Producto inválido. No se agregó al carrito."
                self.success_message = ""
                return
        except Exception:
            self.error_message = "Producto inválido. No se agregó al carrito."
            self.success_message = ""
            return

        user_id = await UsersState.get_user_id()
        if not user_id:
            self.error_message = "Debes iniciar sesión para agregar al carrito."
            self.success_message = ""
            return
        agregar_producto_service(user_id, producto_id)
        self.success_message = "Producto agregado al carrito ✅"
        self.error_message = ""

    @rx.event
    def ir_a_carrito(self):
        return rx.redirect("/carrito")

    @rx.event
    def ir_a_ubicacion(self):
        return rx.redirect("/ubicacion")

    @rx.event
    def ir_a_consulta(self):
        return rx.redirect("/consulta_usuario")

    @rx.event
    def ir_a_login(self):
        return rx.redirect("/users")