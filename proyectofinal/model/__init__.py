"""Modelos de la base de datos.

Importar todo desde aca garantiza que ``SQLModel.metadata`` (y Alembic)
conozcan todas las tablas. Incluye los modelos del plugin de autenticacion
(`LocalUser`, `LocalAuthSession`) porque sus tablas son parte del esquema
(D-019).
"""

from reflex_local_auth import LocalUser
from reflex_local_auth.auth_session import LocalAuthSession

from proyectofinal.model.categoria_modelo import Categoria
from proyectofinal.model.perfil_modelo import UserProfile
from proyectofinal.model.product_model import Producto
from proyectofinal.model.stock_model import Stocks
from proyectofinal.model.carrito_model import Carrito
from proyectofinal.model.pedido_model import Pedido
from proyectofinal.model.pedido_item_modelo import PedidoItem
from proyectofinal.model.consulta_model import Consulta
from proyectofinal.model.ubicacion_model import UbicacionLocal

__all__ = [
    "LocalUser",
    "LocalAuthSession",
    "Categoria",
    "UserProfile",
    "Producto",
    "Stocks",
    "Carrito",
    "Pedido",
    "PedidoItem",
    "Consulta",
    "UbicacionLocal",
]
