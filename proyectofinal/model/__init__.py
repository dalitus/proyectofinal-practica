"""Modelos de la base de datos.

Importar todos los modelos desde aca garantiza que ``SQLModel.metadata``
(y el chequeo de esquema que hace Reflex al arrancar) conozca todas las
tablas, aunque la app no las use todavia. El orden respeta las relaciones
entre modelos.
"""

from proyectofinal.model.users_model import Users
from proyectofinal.model.gerente_model import Gerente
from proyectofinal.model.product_model import Producto
from proyectofinal.model.stock_model import Stocks
from proyectofinal.model.carrito_model import Carrito
from proyectofinal.model.pedido_model import Pedido
from proyectofinal.model.consulta_model import Consulta
from proyectofinal.model.detalle_model import Detalles
from proyectofinal.model.envio_model import Envios
from proyectofinal.model.presupuesto_model import Presupuestos
from proyectofinal.model.solicitan_model import Solicitan
from proyectofinal.model.ubicacion_model import UbicacionLocal

__all__ = [
    "Users",
    "Gerente",
    "Producto",
    "Stocks",
    "Carrito",
    "Pedido",
    "Consulta",
    "Detalles",
    "Envios",
    "Presupuestos",
    "Solicitan",
    "UbicacionLocal",
]
