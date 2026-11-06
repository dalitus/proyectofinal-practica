"""Categorias del catalogo (D-023).

Administrable desde el panel: el producto referencia la categoria por id para
que un typo no rompa el filtro. La marca sigue siendo texto libre en Producto.
"""

from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.model.producto_modelo import Producto


class Categoria(SQLModel, table=True):
    __tablename__ = "categorias"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(unique=True, index=True)

    productos: List["Producto"] = Relationship(back_populates="categoria")
