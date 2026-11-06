from datetime import datetime

from sqlalchemy import Column, Text
from sqlmodel import Field, SQLModel


class Consulta(SQLModel, table=True):
    """Consulta de un comprador; la responde un administrador (D-019).

    No hay tabla `gerentes`: quien responde es otro `LocalUser` con
    `UserProfile.is_admin = True`.
    """

    __tablename__ = "consultas"

    id_consulta: int | None = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="localuser.id", index=True)
    respondido_por_id: int | None = Field(default=None, foreign_key="localuser.id", index=True)

    asunto: str = Field(index=True)
    # TEXT: 255 caracteres no alcanzan y MySQL corta con error en vez de truncar
    # (D-048). El tope real lo valida el servicio.
    mensaje: str = Field(sa_column=Column(Text, nullable=False))

    respuesta: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )
    fecha_creacion: datetime = Field(default_factory=datetime.now)
    fecha_respuesta: datetime | None = None
