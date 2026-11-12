"""Lineas del pedido con snapshot de la compra (D-029).

Cada linea guarda el color, el talle y el precio unitario del momento de la
compra: si el producto cambia de precio o se desactiva, el pedido historico no
cambia. El stock se descuenta en la variante (`Stocks`), que es la combinacion
(producto, color, talle) de D-009.
"""

from decimal import Decimal

from sqlmodel import Field, SQLModel


class PedidoItem(SQLModel, table=True):
    __tablename__ = "lineas_pedido"

    id: int | None = Field(default=None, primary_key=True)
    pedido_id: int = Field(foreign_key="pedidos.id_pedido", index=True)
    variante_id: int = Field(foreign_key="stocks.id_stock", index=True)

    color: str
    talle: str
    cantidad: int = Field(ge=1)
    precio_unitario: Decimal
