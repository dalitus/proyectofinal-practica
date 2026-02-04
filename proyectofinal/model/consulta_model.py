from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Consulta(SQLModel, table=True):
    __tablename__ = "consultas"

    id_consulta: Optional[int] = Field(default=None, primary_key=True)
    asunto: str
    mensaje: str
    respuesta: Optional[str] = None
    id_users: int
    id_gerente: Optional[int] = None
    fecha_creacion: Optional[str] = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    fecha_respuesta: Optional[str] = None