from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlmodel import Field, SQLModel


class Pedido(SQLModel, table=True):
    """Pedido de un comprador registrado.

    Los datos de entrega se copian al crear el pedido; las lineas viven en
    `PedidoItem` con el snapshot de color, talle y precio (D-029). `total` se
    guarda calculado como suma de `cantidad * precio_unitario`.
    """

    __tablename__ = "pedidos"

    id_pedido: Optional[int] = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="localuser.id", index=True)

    estado: str = Field(default="en espera", index=True)
    total: Decimal
    fecha_pedido: datetime = Field(default_factory=datetime.now)
    fecha_entrega: Optional[datetime] = None
    fecha_cancelacion: Optional[datetime] = None

    direccion: str = ""
    numero: str = ""
    departamento: str = ""
    codigo_postal: str = ""
    ciudad: str = ""
    provincia: str = ""
