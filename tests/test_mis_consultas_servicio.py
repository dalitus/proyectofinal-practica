"""Tests de las consultas del comprador (T-065, D-002, D-030).

Se prueba el alta y el alcance de la lista: el autor sale del token en el
estado, pero el servicio es quien decide que un usuario no vea filas ajenas.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from sqlmodel import Session, select

from app.model.consulta_model import Consulta
from app.service.auth_servicio import (
    crear_admin_si_no_existe,
    perfil_por_email,
    registrar_comprador,
)
from app.service.consulta_servicio import (
    MAXIMO_ASUNTO,
    MAXIMO_MENSAJE,
    ErrorDeConsulta,
    crear,
    listar_mis_consultas,
)


def _comprador(email: str = "ana@example.com", nombre: str = "Ana") -> int:
    return registrar_comprador(
        email=email,
        password="secreto123",
        nombre=nombre,
        apellido="Perez",
    ).local_user_id


def _admin(email: str = "admin@example.com") -> int:
    crear_admin_si_no_existe(email=email, password="admin1234", nombre="Admin")
    perfil = perfil_por_email(email)
    assert perfil is not None
    return perfil.local_user_id


def _consulta(
    session: Session,
    *,
    usuario_id: int,
    asunto: str = "Consulta de talle",
    mensaje: str = "Necesito saber si el 42 queda chico.",
    respuesta: str | None = None,
    respondido_por_id: int | None = None,
    fecha: datetime | None = None,
) -> int:
    consulta = Consulta(
        usuario_id=usuario_id,
        asunto=asunto,
        mensaje=mensaje,
        respuesta=respuesta,
        respondido_por_id=respondido_por_id,
        fecha_respuesta=datetime.now() if respuesta else None,
    )
    if fecha is not None:
        consulta.fecha_creacion = fecha
    session.add(consulta)
    session.commit()
    session.refresh(consulta)
    consulta_id = consulta.id_consulta or 0
    session.rollback()
    return consulta_id


def test_crear_guarda_la_consulta_del_usuario(session: Session) -> None:
    usuario_id = _comprador()

    consulta_id = crear(usuario_id, "  Talle 42  ", "  Queda chico o grande?  ")

    fila = session.get(Consulta, consulta_id)
    assert fila is not None
    assert fila.usuario_id == usuario_id
    assert fila.asunto == "Talle 42"
    assert fila.mensaje == "Queda chico o grande?"
    assert fila.respuesta is None
    assert fila.fecha_creacion is not None


@pytest.mark.parametrize(
    ("asunto", "mensaje", "esperado"),
    [
        ("", "Hola", "Escribi un asunto."),
        ("   ", "Hola", "Escribi un asunto."),
        ("Talle", "", "Escribi tu consulta."),
        ("Talle", "   ", "Escribi tu consulta."),
        ("x" * (MAXIMO_ASUNTO + 1), "Hola", "asunto"),
        ("Talle", "x" * (MAXIMO_MENSAJE + 1), "consulta"),
    ],
)
def test_crear_valida_asunto_y_mensaje(
    session: Session,
    asunto: str,
    mensaje: str,
    esperado: str,
) -> None:
    usuario_id = _comprador()

    with pytest.raises(ErrorDeConsulta) as error:
        crear(usuario_id, asunto, mensaje)

    assert esperado in str(error.value)


def test_crear_sin_sesion_no_escribe(session: Session) -> None:
    with pytest.raises(ErrorDeConsulta):
        crear(0, "Talle", "Hola")

    assert session.exec(select(Consulta)).all() == []


def test_listado_solo_trae_las_consultas_propias(session: Session) -> None:
    ana = _comprador()
    beto = _comprador(email="beto@example.com", nombre="Beto")
    _consulta(session, usuario_id=ana, asunto="De Ana")
    _consulta(session, usuario_id=beto, asunto="De Beto")

    pagina = listar_mis_consultas(ana)

    assert pagina.total == 1
    assert [consulta.asunto for consulta in pagina.consultas] == ["De Ana"]


def test_listado_muestra_la_respuesta_y_quien_respondio(session: Session) -> None:
    ana = _comprador()
    admin = _admin()
    _consulta(
        session,
        usuario_id=ana,
        respuesta="El 42 es fiel al talle.",
        respondido_por_id=admin,
    )

    consulta = listar_mis_consultas(ana).consultas[0]

    assert consulta.estado == "respondida"
    assert consulta.estado_etiqueta == "Respondida"
    assert consulta.respuesta == "El 42 es fiel al talle."
    assert consulta.respondida_por == "Admin"
    assert consulta.fecha_respuesta != ""


def test_listado_pendiente_no_inventa_respuesta(session: Session) -> None:
    ana = _comprador()
    _consulta(session, usuario_id=ana)

    consulta = listar_mis_consultas(ana).consultas[0]

    assert consulta.estado == "pendiente"
    assert consulta.respuesta == ""
    assert consulta.fecha_respuesta == ""


def test_listado_ordena_lo_mas_nuevo_primero(session: Session) -> None:
    ana = _comprador()
    ahora = datetime.now()
    _consulta(session, usuario_id=ana, asunto="Vieja", fecha=ahora - timedelta(days=2))
    _consulta(session, usuario_id=ana, asunto="Nueva", fecha=ahora)

    pagina = listar_mis_consultas(ana)

    assert [consulta.asunto for consulta in pagina.consultas] == ["Nueva", "Vieja"]


def test_listado_pagina_y_reencuadra_fuera_de_rango(session: Session) -> None:
    ana = _comprador()
    for indice in range(12):
        _consulta(session, usuario_id=ana, asunto=f"Consulta {indice}")

    primera = listar_mis_consultas(ana)
    segunda = listar_mis_consultas(ana, pagina=2)
    lejana = listar_mis_consultas(ana, pagina=99)

    assert primera.total == 12
    assert primera.total_paginas == 2
    assert len(primera.consultas) == 10
    assert primera.hay_siguiente is True
    assert len(segunda.consultas) == 2
    assert segunda.pagina == 2
    assert lejana.pagina == 2


def test_listado_sin_sesion_falla(session: Session) -> None:
    with pytest.raises(ErrorDeConsulta):
        listar_mis_consultas(0)
