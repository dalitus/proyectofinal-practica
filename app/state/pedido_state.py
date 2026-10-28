# app/state/pedido_state.py
import reflex as rx
import json
from app.state.data import PedidoAdminData
from app.service.pedido_service import (
    obtener_todos_pedidos,
    obtener_pedidos_usuario,
    actualizar_estado_pedido,
)
from app.state.users_state import UsersState
class PedidoState(rx.State):
    # Listas separadas para admin y usuario
    pedidos_admin: list[PedidoAdminData] = []
    pedidos_usuario: list[PedidoAdminData] = []

    # Estados comunes
    loading: bool = False
    error_message: str = ""
    success_message: str = ""

    id_usuario_actual: int = 0


    @rx.event
    async def get_all_pedidos_admin(self):
        """Carga todos los pedidos para el administrador con datos completos."""
        self.loading = True
        self.error_message = ""
        try:
            pedidos = obtener_todos_pedidos()
            self.pedidos_admin = []
            for p in pedidos:
                try:
                    if isinstance(p["productos_json"], str):
                        p["productos_json"] = json.loads(p["productos_json"]) if p["productos_json"] else []
                except Exception:
                    p["productos_json"] = []
                self.pedidos_admin.append(PedidoAdminData(**p))
        except Exception as e:
            self.error_message = f"Error al obtener pedidos admin: {str(e)}"
        finally:
            self.loading = False

    @rx.event
    async def get_all_pedidos_usuario(self, id_usuario: int):
        """Carga los pedidos de un usuario específico."""
        self.loading = True
        self.error_message = ""
        try:
            pedidos = obtener_pedidos_usuario(id_usuario)
            self.pedidos_usuario = []
            for p in pedidos:
                try:
                    if isinstance(p["productos_json"], str):
                        p["productos_json"] = json.loads(p["productos_json"]) if p["productos_json"] else []
                except Exception:
                    p["productos_json"] = []
                self.pedidos_usuario.append(PedidoAdminData(**p))
        except Exception as e:
            self.error_message = f"Error al obtener pedidos usuario: {str(e)}"
        finally:
            self.loading = False

    @rx.event
    async def cambiar_estado_pedido(self, id_pedido: int, nuevo_estado: str):
        """Permite al admin cambiar el estado de un pedido."""
        try:
            ok = actualizar_estado_pedido(id_pedido, nuevo_estado)
            if ok:
                self.success_message = f"Pedido #{id_pedido} actualizado a: {nuevo_estado}"
                await self.get_all_pedidos_admin()
                self.pedidos_admin = [*self.pedidos_admin]  # fuerza re-render
            else:
                self.error_message = f"No se encontró el pedido #{id_pedido}"
        except Exception as e:
            self.error_message = f"Error al actualizar pedido: {str(e)}"


    @rx.event
    async def cargar_pedidos_usuario(self):
        # El id vive en UsersState (por sesión). `app_globals` es un global de
        # módulo que mezcla sesiones, así que no se usa acá.
        users_state = await self.get_state(UsersState)
        user_id = users_state.id or 0
        if user_id > 0:
            await self.get_all_pedidos_usuario(id_usuario=user_id)
            if len(self.pedidos_usuario) == 0:
                self.error_message = "Este usuario no tiene pedidos registrados."
            else:
                self.error_message = ""
        else:
            self.error_message = "Debes iniciar sesión para ver tus pedidos."



