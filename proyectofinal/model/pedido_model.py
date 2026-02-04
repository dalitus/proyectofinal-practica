from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from proyectofinal.model.users_model import Users

class Pedido(SQLModel, table=True):
    __tablename__ = "pedidos"
    
    id_pedido: Optional[int] = Field(default=None, primary_key=True)
    id_users: int = Field(foreign_key="users.id_users")
    estado: str = Field(default="en espera")  # "en espera", "enviado", "entregado"
    total: float
    fecha_pedido: str
    fecha_entrega: Optional[str] = None
    productos_json: str = ""  # Guardar como JSON los productos del pedido
    
    # Datos de ubicación para la entrega
    direccion: Optional[str] = None
    numero: Optional[str] = None
    departamento: Optional[str] = None
    codigo_postal: Optional[str] = None
    ciudad: Optional[str] = None
    provincia: Optional[str] = None
    
    usuario: Optional[Users] = Relationship(back_populates="pedidos")
