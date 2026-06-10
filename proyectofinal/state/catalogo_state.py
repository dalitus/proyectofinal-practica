import reflex as rx
from proyectofinal.state import app_globals
from proyectofinal.service.catalogo_service import (
    obtener_catalogo,
    buscar_en_catalogo
)
from proyectofinal.service.carrito_service import agregar_producto_service


class CatalogoState(rx.State):
    productos: list[dict] = []
    producto_seleccionado: dict = {}
    buscar_texto: str = ""
    error_message: str = ""
    success_message: str = ""

    @rx.event
    def cargar_productos(self):
        """Inicializa la lista de productos al entrar en /catalogo."""
        try:
            self.productos = obtener_catalogo()
            self.error_message = ""
            self.success_message = ""
        except Exception as e:
            self.error_message = f"Error al cargar productos: {e}"
            self.success_message = ""

    @rx.event
    def actualizar_buscar_texto(self, value: str):
        """Actualiza el texto de búsqueda cuando el usuario escribe en el input."""
        self.buscar_texto = value

    @rx.event
    def buscar(self):
        """Ejecuta la búsqueda en el catálogo."""
        try:
            resultados = buscar_en_catalogo(self.buscar_texto)
            if resultados:
                self.productos = resultados
                self.error_message = ""
            else:
                self.productos = []
                self.error_message = "No se encontraron productos."
        except Exception as e:
            self.error_message = f"Error en la búsqueda: {e}"

    @rx.event
    def seleccionar_producto(self, producto: dict):
        """Guarda el producto seleccionado y redirige a su detalle."""
        self.producto_seleccionado = producto
        return rx.redirect(f"/detalle_producto/{producto['id_producto']}")

    @rx.event
    def agregar_carrito_con_id(self, producto_id: int | None):
        print("👉 agregar_carrito_con_id recibió producto_id:", producto_id)
        user_id = app_globals.current_user_id
        print("👉 User ID en CatalogoState:", user_id)

        if user_id is None:
            self.error_message = "Debes iniciar sesión para agregar al carrito."
            self.success_message = ""
            return

        if producto_id is None:
            self.error_message = "El producto no tiene ID válido."
            self.success_message = ""
            return

        try:
            agregar_producto_service(user_id, producto_id)
            self.success_message = "Producto agregado al carrito ✅"
            self.error_message = ""
        except Exception as e:
            self.error_message = f"Error al agregar producto: {e}"
            self.success_message = ""

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