# proyectofinal/model/consulta_model.py
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime
from proyectofinal.model.users_model import Users

class Consulta(SQLModel, table=True):
    __tablename__ = "consultas"

    id_consulta: Optional[int] = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="users.id")
    id_gerente: Optional[int] = Field(default=None, foreign_key="gerentes.id_gerente")

    # Campos obligatorios
    asunto: str = Field(index=True)
    mensaje: str = Field(index=True)

    respuesta: Optional[str] = None
    fecha_creacion: Optional[str] = Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    fecha_respuesta: Optional[str] = None

    # Relación con Users
    usuario: Optional[Users] = Relationship()

