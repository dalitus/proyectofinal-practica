"""Consultas del comprador: lectura y respuesta del admin (T-052, D-019, D-030).

SQL only: no HTTP, no UI, no messages. The service validates and builds the
texts; this module only moves rows.

A question is "pendiente" while ``respuesta`` is empty and "respondida" once the
admin wrote one. The same predicate is used by the page query and by the count,
so the pagination can never disagree with the table.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import aliased
from sqlmodel import select

from app.model.consulta_model import Consulta
from app.model.perfil_modelo import UserProfile
from app.repository.conect_db import get_session


class ConsultaNoEncontrada(Exception):
    """The question id does not exist."""

    def __init__(self, consulta_id: int) -> None:
        super().__init__(consulta_id)
        self.consulta_id = consulta_id


class ConsultaYaRespondida(Exception):
    """The question already has an answer; the admin must not overwrite it."""

    def __init__(self, consulta_id: int) -> None:
        super().__init__(consulta_id)
        self.consulta_id = consulta_id


def _condiciones(estado: str) -> list:
    """WHERE clauses for the pending/answered filter."""
    if estado == "pendiente":
        return [or_(Consulta.respuesta.is_(None), Consulta.respuesta == "")]
    if estado == "respondida":
        return [and_(Consulta.respuesta.is_not(None), Consulta.respuesta != "")]
    return []


def _consulta_comprador_admin():
    """Query skeleton with the buyer and the answering admin, both optional."""
    comprador = aliased(UserProfile)
    administrador = aliased(UserProfile)

    return (
        select(Consulta, comprador, administrador)
        .outerjoin(comprador, comprador.local_user_id == Consulta.usuario_id)
        .outerjoin(
            administrador,
            administrador.local_user_id == Consulta.respondido_por_id,
        )
    )


def listar_consultas(
    *,
    estado: str = "",
    offset: int = 0,
    limite: int = 10,
) -> list[tuple[Consulta, UserProfile | None, UserProfile | None]]:
    """One page of questions, newest first, with the buyer and admin profiles."""
    with get_session() as session:
        consulta = (
            _consulta_comprador_admin()
            .where(*_condiciones(estado))
            .order_by(Consulta.fecha_creacion.desc(), Consulta.id_consulta.desc())
            .offset(offset)
            .limit(limite)
        )
        return [tuple(fila) for fila in session.exec(consulta).all()]  # type: ignore[misc]


def contar_consultas(*, estado: str = "") -> int:
    """Total of questions matching the same filter as the page query."""
    with get_session() as session:
        return session.exec(
            select(func.count()).select_from(Consulta).where(*_condiciones(estado))
        ).one()


def obtener_consulta(
    consulta_id: int,
) -> tuple[Consulta, UserProfile | None, UserProfile | None] | None:
    """One question with both profiles, or ``None``."""
    with get_session() as session:
        fila = session.exec(
            _consulta_comprador_admin().where(Consulta.id_consulta == consulta_id)
        ).first()
        return tuple(fila) if fila else None  # type: ignore[misc]


def responder(
    *,
    consulta_id: int,
    respuesta: str,
    admin_id: int,
    ahora: datetime,
) -> None:
    """Store the admin's answer in one transaction.

    The row is locked and rechecked: a double click cannot overwrite an answer
    that another admin already wrote.
    """
    with get_session() as session:
        consulta = session.exec(
            select(Consulta)
            .where(Consulta.id_consulta == consulta_id)
            .with_for_update()
        ).first()

        if consulta is None:
            raise ConsultaNoEncontrada(consulta_id)
        if (consulta.respuesta or "").strip():
            raise ConsultaYaRespondida(consulta_id)

        consulta.respuesta = respuesta
        consulta.respondido_por_id = admin_id
        consulta.fecha_respuesta = ahora

        session.add(consulta)
        session.commit()


def listar_consultas_de_usuario(
    usuario_id: int,
    *,
    offset: int = 0,
    limite: int = 10,
) -> list[tuple[Consulta, UserProfile | None]]:
    """One page of a buyer's own questions with the answering admin (T-065).

    The filter is in SQL, not in the page: asking for another user's id returns
    that user's rows, so the scope is decided here and cannot be widened from
    the browser.
    """
    administrador = aliased(UserProfile)

    with get_session() as session:
        filas = session.exec(
            select(Consulta, administrador)
            .outerjoin(
                administrador,
                administrador.local_user_id == Consulta.respondido_por_id,
            )
            .where(Consulta.usuario_id == usuario_id)
            .order_by(Consulta.fecha_creacion.desc(), Consulta.id_consulta.desc())
            .offset(offset)
            .limit(limite)
        )
        return [tuple(fila) for fila in filas.all()]  # type: ignore[misc]


def contar_consultas_de_usuario(*, usuario_id: int) -> int:
    """Total of questions owned by one buyer, for the pagination."""
    with get_session() as session:
        return session.exec(
            select(func.count())
            .select_from(Consulta)
            .where(Consulta.usuario_id == usuario_id)
        ).one()


def crear_consulta(
    *,
    usuario_id: int,
    asunto: str,
    mensaje: str,
    ahora: datetime,
) -> int:
    """Store a buyer's question and return its id (T-065).

    The author comes from the session token, never from the form (D-002): the
    service passes the id it resolved on the server.
    """
    with get_session() as session:
        consulta = Consulta(
            usuario_id=usuario_id,
            asunto=asunto,
            mensaje=mensaje,
            fecha_creacion=ahora,
        )
        session.add(consulta)
        session.commit()
        session.refresh(consulta)
        return consulta.id_consulta or 0


def eliminar(consulta_id: int) -> None:
    """Delete the question; the admin confirms before calling this (D-030)."""
    with get_session() as session:
        consulta = session.exec(
            select(Consulta)
            .where(Consulta.id_consulta == consulta_id)
            .with_for_update()
        ).first()

        if consulta is None:
            raise ConsultaNoEncontrada(consulta_id)

        session.delete(consulta)
        session.commit()
