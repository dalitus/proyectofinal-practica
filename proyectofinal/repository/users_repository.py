from proyectofinal.model.users_model import Users
from proyectofinal.repository.conect_db import get_session
from proyectofinal.service.security import verify_password
from sqlmodel import select


# Obtener todos los usuarios
def select_all():
    with get_session() as session:
        query = select(Users)
        return session.exec(query).all()

# Buscar por email
def select_by_email(email: str):
    with get_session() as session:
        query = select(Users).where(Users.email == email)
        return session.exec(query).all()

# Crear nuevo usuario
def create_user(user: Users):
    with get_session() as session:
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

# Eliminar por email
def delete_user_by_email(email: str):
    with get_session() as session:
        query = select(Users).where(Users.email == email)
        user = session.exec(query).one()
        session.delete(user)
        session.commit()

# Validar login
def validar_usuario(email: str, contrasena: str):
    with get_session() as session:
        user = session.exec(select(Users).where(Users.email == email)).one_or_none()
        if user and verify_password(contrasena, user.contrasena):
            return user
        return None
    

# Buscar usuario por ID
def get_user_by_id(user_id: int):
    with get_session() as session:
        query = select(Users).where(Users.id_users == user_id)
        return session.exec(query).first()



