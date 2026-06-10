from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from proyectofinal.model.product_model import Producto

class Stocks(SQLModel, table=True):
    __tablename__ = "stocks"

    id_stock: Optional[int] = Field(default=None, primary_key=True)
    producto_id: int = Field(foreign_key="productos.id")   # 👈 corregido
    color: str
    cantidad_disponible: int

    producto: Optional["Producto"] = Relationship(back_populates="stocks")