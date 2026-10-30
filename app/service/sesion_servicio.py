"""Session token to user id (T-020, T-040).

``LocalAuthState`` keeps the session token in the browser local storage and the
plugin table ``localauthsession`` maps that token to a ``LocalUser``. The cart is
stored per user (D-002, D-008), so the server needs that id: the state asks here
instead of opening a session or importing the engine (D-033, T-062).

The token is the only thing that travels from the client. The user id never comes
from the browser, so a session cannot be impersonated by editing a state var.
"""

from __future__ import annotations

from datetime import datetime, timezone

from reflex_local_auth.local_auth import LocalAuthSession
from sqlmodel import select

from app.repository.conect_db import get_session
from app.service import auth_servicio

# Los tres roles que existen (D-021). El invitado no tiene fila en la base: es la
# ausencia de sesion valida, no un cuarto tipo de cuenta.
INVITADO = "invitado"
COMPRADOR = "comprador"
ADMIN = "admin"
ROLES = (INVITADO, COMPRADOR, ADMIN)


def usuario_autenticado(token: str) -> int | None:
    """Return the ``LocalUser.id`` behind a live token, or ``None``.

    ``None`` covers the three cases that share an answer: no token (guest), an
    unknown token and an expired session.
    """
    limpio = (token or "").strip()
    if not limpio:
        return None

    with get_session() as session:
        usuario_id = session.exec(
            select(LocalAuthSession.user_id).where(
                LocalAuthSession.session_id == limpio,
                LocalAuthSession.expiration >= datetime.now(timezone.utc),
            )
        ).first()

    return int(usuario_id) if usuario_id is not None else None


def rol(token: str) -> str:
    """Return ``invitado``, ``comprador`` or ``admin`` for a session token.

    The role is read from the database on every call: hiding a button is not a
    permission (D-021). A session without a profile counts as ``comprador``; an
    admin is only a profile with ``is_admin`` (D-013).
    """
    usuario_id = usuario_autenticado(token)
    if usuario_id is None:
        return INVITADO

    perfil = auth_servicio.obtener_perfil(usuario_id)
    if perfil is not None and perfil.is_admin:
        return ADMIN
    return COMPRADOR


def es_admin(token: str) -> bool:
    """Shorthand for the admin guard: the only role allowed in the panel."""
    return rol(token) == ADMIN


def usuario_con_rol(token: str, *permitidos: str) -> int | None:
    """Return the user id when its live role is allowed, or ``None``.

    The caller redirects on ``None``: a guest to the login and a logged-in user
    without permission to the 403 page (D-021). Passing no roles allows every
    authenticated user, which is what the buyer screens need.
    """
    usuario_id = usuario_autenticado(token)
    if usuario_id is None:
        return None

    if permitidos:
        perfil = auth_servicio.obtener_perfil(usuario_id)
        actual = ADMIN if perfil is not None and perfil.is_admin else COMPRADOR
        if actual not in permitidos:
            return None

    return usuario_id
