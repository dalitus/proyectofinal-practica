from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.model.categoria_modelo import Categoria
    from app.model.variante_modelo import Stocks


class Producto(SQLModel, table=True):
    """Producto del catalogo.

    El talle no vive aca: cada combinacion (color, talle) es una variante con su
    propio stock (D-009). La categoria se referencia por id (D-023) y el borrado
    es logico con `activo` (D-028).
    """

    __tablename__ = "productos"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(index=True)
    descripcion: str = ""
    marca: str = Field(default="", index=True)
    precio: Decimal
    categoria_id: int = Field(foreign_key="categorias.id", index=True)
    activo: bool = Field(default=True, index=True)
    imagen: str | None = None

    categoria: Optional["Categoria"] = Relationship(back_populates="productos")
    stocks: list["Stocks"] = Relationship(back_populates="producto")

    @property
    def cantidad_total(self) -> int:
        return sum(s.cantidad_disponible for s in self.stocks)
