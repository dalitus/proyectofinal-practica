from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Consulta(SQLModel, table=True):
    """Consulta de un comprador; la responde un administrador (D-019).

    No hay tabla `gerentes`: quien responde es otro `LocalUser` con
    `UserProfile.is_admin = True`.
    """

    __tablename__ = "consultas"

    id_consulta: Optional[int] = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="localuser.id", index=True)
    respondido_por_id: Optional[int] = Field(
        default=None, foreign_key="localuser.id", index=True
    )

    asunto: str = Field(index=True)
    mensaje: str

    respuesta: Optional[str] = None
    fecha_creacion: datetime = Field(default_factory=datetime.now)
    fecha_respuesta: Optional[datetime] = None
