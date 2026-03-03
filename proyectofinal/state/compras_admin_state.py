import reflex as rx
from proyectofinal.service.pedido_service import obtener_todos_pedidos
from proyectofinal.state.data import PedidoAdminData

class ComprasAdminState(rx.State):
    pedidos: list[PedidoAdminData] = []
    loading: bool = False
    error_message: str = ""

    @rx.event
    async def cargar_pedidos_admin(self):
        try:
            self.loading = True
            pedidos_data = obtener_todos_pedidos()
            self.pedidos = [PedidoAdminData(**p) for p in pedidos_data]
            self.error_message = ""
        except Exception as e:
            self.error_message = f"Error al cargar pedidos: {str(e)}"
        finally:
            self.loading = False