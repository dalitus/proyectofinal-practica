from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from decimal import Decimal

if TYPE_CHECKING:
    from proyectofinal.model.stock_model import Stocks
    from proyectofinal.model.carrito_model import Carrito

class Producto(SQLModel, table=True):
    __tablename__ = "productos"

    id_producto: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    descripcion: str
    precio: Decimal
    marca: str
    categoria: str
    talle: str
    imagen: Optional[str] = None

    stocks: List["Stocks"] = Relationship(back_populates="producto")
    carritos: List["Carrito"] = Relationship(back_populates="producto")

    # 👇 cantidad total calculada
    @property
    def cantidad_total(self) -> int:
        return sum(s.cantidad_disponible for s in self.stocks)


