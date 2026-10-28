"""Perfil del usuario comprador o administrador (D-019).

`LocalUser` (plugin) guarda credenciales; este perfil guarda los datos de la
persona y el rol. El administrador se marca con `is_admin = True` en lugar de
vivir en una tabla `gerentes` aparte.
"""

from typing import Optional

from sqlmodel import Field, SQLModel


class UserProfile(SQLModel, table=True):
    __tablename__ = "user_profiles"

    id: Optional[int] = Field(default=None, primary_key=True)
    local_user_id: int = Field(foreign_key="localuser.id", unique=True, index=True)

    nombre: str
    apellido: str = ""
    email: str = Field(unique=True, index=True)
    telefono: str = ""
    direccion: str = ""
    is_admin: bool = Field(default=False, index=True)
