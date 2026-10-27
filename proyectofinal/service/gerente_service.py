from proyectofinal.model.gerente_model import Gerente
from proyectofinal.repository.conect_db import get_session
from proyectofinal.service.security import verify_password


def validar_admin_service(email: str, contrasenia: str) -> Gerente:
    """Return the admin matching the credentials, or raise ValueError."""
    with get_session() as db:
        admin = db.query(Gerente).filter(Gerente.email == email).first()
        if admin and verify_password(contrasenia, admin.contrasenia):
            return admin

    raise ValueError("Email o contraseña incorrectos")
