import reflex as rx
import json
from proyectofinal.state.data import PedidoData, PedidoAdminData
from proyectofinal.service.pedido_service import (
    obtener_pedidos_usuario,
    obtener_todos_pedidos,
    actualizar_estado_pedido,
)

class PedidoState(rx.State):
    # 👇 Tipamos la lista con el modelo correcto
    pedidos: list[PedidoAdminData] = []   # para admin
    # Si querés también la vista usuario, podés usar list[PedidoData]

    loading: bool = False
    error_message: str = ""
    success_message: str = ""

    @rx.event
    async def get_all_pedidos(self, id_usuario: int):
        """Carga pedidos del usuario."""
        self.loading = True
        self.error_message = ""
        try:
            pedidos = obtener_pedidos_usuario(id_usuario)
            self.pedidos = []
            for p in pedidos:
                try:
                    if isinstance(p["productos_json"], str):
                        p["productos_json"] = json.loads(p["productos_json"]) if p["productos_json"] else []
                except Exception:
                    p["productos_json"] = []
                # Usuario usa PedidoData
                self.pedidos.append(PedidoData(**p))
        except Exception as e:
            self.error_message = f"Error al obtener pedidos: {str(e)}"
        finally:
            self.loading = False

    @rx.event
    async def get_all_pedidos_admin(self):
        """Carga pedidos para el administrador con datos completos."""
        self.loading = True
        self.error_message = ""
        try:
            pedidos = obtener_todos_pedidos()
            self.pedidos = []
            for p in pedidos:
                try:
                    if isinstance(p["productos_json"], str):
                        p["productos_json"] = json.loads(p["productos_json"]) if p["productos_json"] else []
                except Exception:
                    p["productos_json"] = []
                # Admin usa PedidoAdminData
                self.pedidos.append(PedidoAdminData(**p))
        except Exception as e:
            self.error_message = f"Error al obtener pedidos admin: {str(e)}"
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
                self.pedidos = [*self.pedidos]  # fuerza re-render
            else:
                self.error_message = f"No se encontró el pedido #{id_pedido}"
        except Exception as e:
            self.error_message = f"Error al actualizar pedido: {str(e)}"