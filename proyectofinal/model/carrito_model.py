from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from proyectofinal.model.product_model import Producto
from proyectofinal.model.users_model import Users

class Carrito(SQLModel, table=True):
    __tablename__ = "carritos"

    # Clave primaria
    id_carrito: Optional[int] = Field(default=None, primary_key=True)

    # Foreign keys normalizadas
    usuario_id: int = Field(foreign_key="users.id")       # antes id_users
    producto_id: int = Field(foreign_key="productos.id")  # antes id_producto

    cantidad: int = Field(default=1)

    # Relaciones
    usuario: Optional[Users] = Relationship(back_populates="carritos")
    producto: Optional[Producto] = Relationship(back_populates="carritos")
