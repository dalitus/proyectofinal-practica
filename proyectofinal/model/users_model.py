import reflex as rx
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from proyectofinal.model.carrito_model import Carrito
    from proyectofinal.model.pedido_model import Pedido

class Users(SQLModel, table=True):
    __tablename__ = "users"

    # Clave primaria normalizada
    id: Optional[int] = Field(default=None, primary_key=True)

    # Campos de usuario
    nombre: str
    apellido: str
    contrasena: str
    email: str
    telefono: str
    direccion: str = ""

    # Relaciones
    carritos: List["Carrito"] = Relationship(back_populates="usuario")
    pedidos: List["Pedido"] = Relationship(back_populates="usuario")