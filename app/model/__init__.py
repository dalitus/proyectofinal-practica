"""Modelos de la base de datos.

Importar todo desde aca garantiza que ``SQLModel.metadata`` (y Alembic)
conozcan todas las tablas. Incluye los modelos del plugin de autenticacion
(`LocalUser`, `LocalAuthSession`) porque sus tablas son parte del esquema
(D-019).
"""

from reflex_local_auth import LocalUser
from reflex_local_auth.auth_session import LocalAuthSession

from app.model.categoria_modelo import Categoria
from app.model.perfil_modelo import UserProfile
from app.model.product_model import Producto
from app.model.stock_model import Stocks
from app.model.carrito_model import Carrito
from app.model.pedido_model import Pedido
from app.model.pedido_item_modelo import PedidoItem
from app.model.consulta_model import Consulta
from app.model.ubicacion_model import UbicacionLocal

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
