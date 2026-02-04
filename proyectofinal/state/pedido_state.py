import reflex as rx
from typing import Optional
from proyectofinal.model.pedido_model import Pedido

class PedidoState(rx.State):
    pedidos: list[dict] = []
    loading: bool = False
    error_message: str = ""
    success_message: str = ""
    user_id_actual: int = 0
    
    @rx.event
    async def get_all_pedidos(self):
        """Obtener todos los pedidos del usuario logueado"""
        try:
            self.loading = True
            from proyectofinal.service.pedido_service import obtener_pedidos_usuario
            from proyectofinal.state.users_state import UsersState
            
            # Obtener el user_id usando el método asincrónico de UsersState
            user_id = await UsersState.get_user_id()
            
            if not user_id:
                self.error_message = "Usuario no autenticado. Por favor, inicia sesión."
                self.pedidos = []
            else:
                self.user_id_actual = user_id
                self.pedidos = obtener_pedidos_usuario(user_id)
                self.error_message = ""
        except Exception as e:
            import traceback
            self.error_message = f"Error al cargar pedidos: {str(e)}"
            print(f"[PEDIDO] Error: {e}")
            traceback.print_exc()
        finally:
            self.loading = False
    
    @rx.event
    def get_all_pedidos_admin(self):
        """Obtener TODOS los pedidos para admin (sin filtro de usuario)"""
        try:
            self.loading = True
            from proyectofinal.service.pedido_service import obtener_todos_pedidos
            
            # Cargar todos los pedidos sin filtro
            self.pedidos = obtener_todos_pedidos()
            self.error_message = ""
        except Exception as e:
            import traceback
            self.error_message = f"Error al cargar pedidos: {str(e)}"
            print(f"[PEDIDO ADMIN] Error: {e}")
            traceback.print_exc()
        finally:
            self.loading = False
    
    def cambiar_estado_pedido(self, id_pedido: int, nuevo_estado: str):
        """Cambiar el estado del pedido"""
        try:
            from proyectofinal.service.pedido_service import actualizar_estado_pedido
            
            actualizar_estado_pedido(id_pedido, nuevo_estado)
            self.success_message = f"Pedido actualizado a: {nuevo_estado}"
            self.get_all_pedidos_admin()
        except Exception as e:
            self.error_message = f"Error al actualizar pedido: {str(e)}"
