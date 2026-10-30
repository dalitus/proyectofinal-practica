"""Tests del rol de la sesión (T-023, D-021).

El rol sale de la base en cada llamada: ocultar un botón no es un permiso. Estas
pruebas cubren las tres respuestas posibles y la guarda que usan las páginas.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from reflex_local_auth.local_auth import LocalAuthSession
from sqlmodel import Session

from app.service.auth_servicio import (
    crear_admin_si_no_existe,
    perfil_por_email,
    registrar_comprador,
)
from app.service.sesion_servicio import (
    ADMIN,
    COMPRADOR,
    INVITADO,
    es_admin,
    rol,
    usuario_con_rol,
)


def _comprador(session: Session, email: str = "ana@example.com") -> int:
    usuario_id = registrar_comprador(
        email=email,
        password="secreto123",
        nombre="Ana",
        apellido="Perez",
    ).local_user_id
    session.rollback()
    return usuario_id


def _admin(session: Session, email: str = "admin@example.com") -> int:
    crear_admin_si_no_existe(email=email, password="admin1234", nombre="Admin")
    perfil = perfil_por_email(email)
    assert perfil is not None
    session.rollback()
    return perfil.local_user_id


def _token(
    session: Session,
    *,
    usuario_id: int,
    session_id: str,
    vence_en: timedelta = timedelta(hours=1),
) -> str:
    session.add(
        LocalAuthSession(
            user_id=usuario_id,
            session_id=session_id,
            expiration=datetime.now(timezone.utc) + vence_en,
        )
    )
    session.commit()
    session.rollback()
    return session_id


def test_sin_token_es_invitado() -> None:
    assert rol("") == INVITADO
    assert rol("   ") == INVITADO
    assert es_admin("") is False


def test_token_desconocido_es_invitado() -> None:
    assert rol("token-que-no-existe") == INVITADO


def test_sesion_expirada_es_invitado(session: Session) -> None:
    usuario_id = _comprador(session)
    token = _token(
        session,
        usuario_id=usuario_id,
        session_id="vencida",
        vence_en=timedelta(hours=-1),
    )

    assert rol(token) == INVITADO


def test_comprador_no_es_admin(session: Session) -> None:
    usuario_id = _comprador(session)
    token = _token(session, usuario_id=usuario_id, session_id="sesion-comprador")

    assert rol(token) == COMPRADOR
    assert es_admin(token) is False


def test_admin_es_admin(session: Session) -> None:
    usuario_id = _admin(session)
    token = _token(session, usuario_id=usuario_id, session_id="sesion-admin")

    assert rol(token) == ADMIN
    assert es_admin(token) is True


def test_guarda_permite_solo_el_rol_pedido(session: Session) -> None:
    comprador_id = _comprador(session)
    admin_id = _admin(session)
    token_comprador = _token(session, usuario_id=comprador_id, session_id="c1")
    token_admin = _token(session, usuario_id=admin_id, session_id="a1")

    assert usuario_con_rol(token_comprador, ADMIN) is None
    assert usuario_con_rol(token_admin, ADMIN) == admin_id
    assert usuario_con_rol(token_admin, COMPRADOR) is None


def test_guarda_sin_roles_pide_solo_estar_logueado(session: Session) -> None:
    administrador_id = _admin(session)
    token = _token(session, usuario_id=administrador_id, session_id="a2")

    assert usuario_con_rol(token) == administrador_id
    assert usuario_con_rol("", COMPRADOR) is None


def test_una_cuenta_sin_perfil_no_es_admin(session: Session) -> None:
    """Un ``LocalUser`` sin fila en ``UserProfile`` no puede tener rol admin."""
    from reflex_local_auth.local_auth import LocalUser

    usuario = LocalUser(
        username="sin-perfil@example.com",
        password_hash=LocalUser.hash_password("secreto123"),
        enabled=True,
    )
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    token = _token(session, usuario_id=usuario.id or 0, session_id="huerfana")

    assert rol(token) == COMPRADOR
    assert es_admin(token) is False
