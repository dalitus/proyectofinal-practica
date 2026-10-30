"""Registro, perfil y bootstrap del administrador (D-013, D-018, D-019, D-033).

La identidad vive en dos tablas: ``LocalUser`` (credenciales y hash bcrypt, del
plugin) y ``UserProfile`` (datos de la persona y rol). Las reglas de alta estan
aca, no en el estado de Reflex: el estado solo llama a estas funciones.

Cada funcion publica abre y cierra su propia sesion (D-033). Los tests no tocan
la base de desarrollo: inyectan el engine de ``zapateria_test``.
"""

from __future__ import annotations

import re

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from reflex_local_auth import LocalUser

from app.model.perfil_modelo import UserProfile
from app.repository.conect_db import get_session

MIN_PASSWORD_LENGTH = 8
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ErrorDeRegistro(ValueError):
    """Datos invalidos o email ya usado al crear una cuenta."""


class ErrorDeAcceso(ValueError):
    """Credenciales invalidas o cuenta deshabilitada al iniciar sesion (T-021)."""


# El mismo texto para email inexistente y contrasena equivocada: el formulario
# no revela si la cuenta existe (T-021).
MENSAJE_CREDENCIALES = "El email o la contraseña no son correctos."
MENSAJE_CUENTA_DESHABILITADA = "Esta cuenta está deshabilitada. Escribinos para reactivarla."


def normalizar_email(email: str) -> str:
    """Return the email trimmed and lowercased, validating its shape."""
    limpio = (email or "").strip().lower()
    if not EMAIL_PATTERN.match(limpio):
        raise ErrorDeRegistro("Ingresá un email válido.")
    return limpio


def validar_password(password: str) -> str:
    """Return the password unchanged if it meets the minimum rules."""
    if not password or len(password) < MIN_PASSWORD_LENGTH:
        raise ErrorDeRegistro(
            f"La contraseña necesita al menos {MIN_PASSWORD_LENGTH} caracteres."
        )
    return password


def _buscar_usuario(session: Session, email: str) -> LocalUser | None:
    return session.exec(select(LocalUser).where(LocalUser.username == email)).one_or_none()


def _crear_cuenta(
    session: Session,
    *,
    email: str,
    password: str,
    nombre: str,
    apellido: str,
    telefono: str,
    direccion: str,
    is_admin: bool,
) -> UserProfile:
    """Create ``LocalUser`` + ``UserProfile`` in a single transaction."""
    if _buscar_usuario(session, email) is not None:
        raise ErrorDeRegistro("Ya existe una cuenta con ese email.")

    usuario = LocalUser(
        username=email,
        password_hash=LocalUser.hash_password(password),
        enabled=True,
    )
    session.add(usuario)

    try:
        session.flush()

        perfil = UserProfile(
            local_user_id=usuario.id,
            nombre=nombre.strip() or email,
            apellido=apellido.strip(),
            email=email,
            telefono=telefono.strip(),
            direccion=direccion.strip(),
            is_admin=is_admin,
        )
        session.add(perfil)
        session.commit()
    except IntegrityError as error:  # carrera entre validar e insertar
        session.rollback()
        raise ErrorDeRegistro("Ya existe una cuenta con ese email.") from error

    session.refresh(perfil)
    return perfil


def registrar_comprador(
    *,
    email: str,
    password: str,
    nombre: str = "",
    apellido: str = "",
    telefono: str = "",
    direccion: str = "",
) -> UserProfile:
    """Register a buyer account; the public form can never create an admin."""
    with get_session() as session:
        return _crear_cuenta(
            session,
            email=normalizar_email(email),
            password=validar_password(password),
            nombre=nombre,
            apellido=apellido,
            telefono=telefono,
            direccion=direccion,
            is_admin=False,
        )


def autenticar(*, email: str, password: str) -> int:
    """Return the ``LocalUser.id`` when the credentials are valid (T-021).

    The message is the same for an unknown email and a wrong password, so the
    form never reveals whether an account exists. A disabled account gets its
    own message because its owner has to ask the store to reactivate it.
    """
    limpio = (email or "").strip().lower()
    if not limpio or not password:
        raise ErrorDeAcceso(MENSAJE_CREDENCIALES)

    with get_session() as session:
        usuario = _buscar_usuario(session, limpio)
        if usuario is None:
            raise ErrorDeAcceso(MENSAJE_CREDENCIALES)
        if not usuario.enabled:
            raise ErrorDeAcceso(MENSAJE_CUENTA_DESHABILITADA)
        if not usuario.verify(password):
            raise ErrorDeAcceso(MENSAJE_CREDENCIALES)
        if usuario.id is None:  # leido de la DB: el id siempre existe
            raise ErrorDeAcceso(MENSAJE_CREDENCIALES)
        return usuario.id


def crear_admin_si_no_existe(
    *,
    email: str,
    password: str,
    nombre: str = "Administrador",
) -> bool:
    """Create the bootstrap admin. Returns False when it already existed (D-013)."""
    limpio = normalizar_email(email)
    with get_session() as session:
        if _buscar_usuario(session, limpio) is not None:
            return False

        _crear_cuenta(
            session,
            email=limpio,
            password=validar_password(password),
            nombre=nombre,
            apellido="",
            telefono="",
            direccion="",
            is_admin=True,
        )
    return True


def obtener_perfil(local_user_id: int) -> UserProfile | None:
    """Return the profile for a ``LocalUser`` id, if it exists."""
    with get_session() as session:
        return session.exec(
            select(UserProfile).where(UserProfile.local_user_id == local_user_id)
        ).one_or_none()


def perfil_por_email(email: str) -> UserProfile | None:
    """Return the profile for an email, if it exists."""
    try:
        limpio = normalizar_email(email)
    except ErrorDeRegistro:
        return None

    with get_session() as session:
        return session.exec(
            select(UserProfile).where(UserProfile.email == limpio)
        ).one_or_none()
