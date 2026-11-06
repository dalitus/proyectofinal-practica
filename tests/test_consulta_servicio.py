"""Tests de las consultas del admin (T-052, D-030).

Se insertan las filas directo: acá se prueba lectura, respuesta, borrado y
filtros, no el alta (que llega con la pantalla del comprador, T-065).
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from sqlmodel import Session

from app.model.consulta_modelo import Consulta
from app.service.auth_servicio import crear_admin_si_no_existe, perfil_por_email, registrar_comprador
from app.service.consulta_servicio import (
    ErrorDeConsulta,
    eliminar,
    listar_consultas,
    obtener_detalle,
    opciones_de_filtro,
    responder,
)


def _comprador(email: str = "ana@example.com", nombre: str = "Ana", apellido: str = "Perez") -> int:
    return registrar_comprador(
        email=email,
        password="secreto123",
        nombre=nombre,
        apellido=apellido,
    ).local_user_id


def _admin(email: str = "admin@example.com", nombre: str = "Admin") -> int:
    crear_admin_si_no_existe(email=email, password="admin1234", nombre=nombre)
    perfil = perfil_por_email(email)
    assert perfil is not None
    assert perfil.is_admin is True
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
    )
    if fecha is not None:
        consulta.fecha_creacion = fecha
    if respuesta:
        consulta.fecha_respuesta = datetime.now()
    session.add(consulta)
    session.commit()
    session.refresh(consulta)
    session.rollback()
    return consulta.id_consulta or 0


def test_listado_trae_comprador_estado_y_fecha(session: Session) -> None:
    usuario_id = _comprador()
    _consulta(session, usuario_id=usuario_id)

    pagina = listar_consultas()

    assert pagina.total == 1
    consulta = pagina.consultas[0]
    assert consulta.cliente == "Ana Perez"
    assert consulta.email == "ana@example.com"
    assert consulta.asunto == "Consulta de talle"
    assert consulta.estado == "pendiente"
    assert consulta.estado_etiqueta == "Pendiente"
    assert consulta.respondida_por == ""
    assert consulta.fecha


def test_el_resumen_recorta_los_mensajes_largos(session: Session) -> None:
    usuario_id = _comprador()
    _consulta(session, usuario_id=usuario_id, mensaje="x" * 300)

    resumen = listar_consultas().consultas[0].resumen

    assert resumen.endswith("...")
    assert len(resumen) <= 143


def test_filtro_pendiente_y_respondida(session: Session) -> None:
    usuario_id = _comprador()
    admin_id = _admin()
    _consulta(session, usuario_id=usuario_id)
    _consulta(session, usuario_id=usuario_id, asunto="Otra duda")
    _consulta(
        session,
        usuario_id=usuario_id,
        asunto="Ya respondida",
        respuesta="Queda bien, pedi el 42.",
        respondido_por_id=admin_id,
    )

    pendientes = listar_consultas(filtro="pendiente")
    respondidas = listar_consultas(filtro="respondida")
    todas = listar_consultas()

    assert (pendientes.total, len(pendientes.consultas)) == (2, 2)
    assert (respondidas.total, len(respondidas.consultas)) == (1, 1)
    assert respondidas.consultas[0].estado_etiqueta == "Respondida"
    assert respondidas.consultas[0].respondida_por == "Admin"
    assert todas.total == 3


def test_filtro_desconocido_se_ignora(session: Session) -> None:
    usuario_id = _comprador()
    _consulta(session, usuario_id=usuario_id)

    pagina = listar_consultas(filtro="archivada")

    assert pagina.filtro == ""
    assert pagina.total == 1


def test_paginacion_de_diez(session: Session) -> None:
    usuario_id = _comprador()
    for numero in range(12):
        _consulta(session, usuario_id=usuario_id, asunto=f"Consulta {numero}")

    primera = listar_consultas(pagina=1)
    segunda = listar_consultas(pagina=2)

    assert primera.total == 12
    assert primera.total_paginas == 2
    assert len(primera.consultas) == 10
    assert primera.hay_siguiente is True
    assert len(segunda.consultas) == 2
    assert segunda.hay_anterior is True


def test_orden_por_fecha_descendente(session: Session) -> None:
    usuario_id = _comprador()
    base = datetime(2026, 1, 1, 10, 0)
    _consulta(session, usuario_id=usuario_id, asunto="Vieja", fecha=base)
    _consulta(
        session,
        usuario_id=usuario_id,
        asunto="Nueva",
        fecha=base + timedelta(days=2),
    )
    _consulta(
        session,
        usuario_id=usuario_id,
        asunto="Del medio",
        fecha=base + timedelta(days=1),
    )

    asuntos = [consulta.asunto for consulta in listar_consultas().consultas]

    assert asuntos == ["Nueva", "Del medio", "Vieja"]


def test_responder_guarda_texto_admin_y_fecha(session: Session) -> None:
    usuario_id = _comprador()
    admin_id = _admin()
    consulta_id = _consulta(session, usuario_id=usuario_id)

    assert responder(consulta_id, "  Te queda bien el 42.  ", admin_id) == "Te queda bien el 42."

    detalle = obtener_detalle(consulta_id)
    assert detalle.estado == "respondida"
    assert detalle.respuesta == "Te queda bien el 42."
    assert detalle.respondida_por == "Admin"
    assert detalle.fecha_respuesta
    assert detalle.cliente == "Ana Perez"


def test_respuesta_vacia_falla(session: Session) -> None:
    usuario_id = _comprador()
    admin_id = _admin()
    consulta_id = _consulta(session, usuario_id=usuario_id)

    with pytest.raises(ErrorDeConsulta) as error:
        responder(consulta_id, "   ", admin_id)

    assert "Escribi una respuesta" in str(error.value)
    assert obtener_detalle(consulta_id).estado == "pendiente"


def test_respuesta_demasiado_larga_falla(session: Session) -> None:
    usuario_id = _comprador()
    admin_id = _admin()
    consulta_id = _consulta(session, usuario_id=usuario_id)

    with pytest.raises(ErrorDeConsulta) as error:
        responder(consulta_id, "x" * 2001, admin_id)

    assert "2000 caracteres" in str(error.value)


def test_no_se_puede_responder_dos_veces(session: Session) -> None:
    usuario_id = _comprador()
    admin_id = _admin()
    consulta_id = _consulta(session, usuario_id=usuario_id)
    responder(consulta_id, "Primera respuesta.", admin_id)

    with pytest.raises(ErrorDeConsulta) as error:
        responder(consulta_id, "Segunda respuesta.", admin_id)

    assert "ya tiene respuesta" in str(error.value)
    assert obtener_detalle(consulta_id).respuesta == "Primera respuesta."


def test_responder_una_consulta_inexistente_falla(session: Session) -> None:
    admin_id = _admin()

    with pytest.raises(ErrorDeConsulta) as error:
        responder(9999, "Hola", admin_id)

    assert "No existe la consulta #9999" in str(error.value)


def test_eliminar_borra_y_despues_falla(session: Session) -> None:
    usuario_id = _comprador()
    consulta_id = _consulta(session, usuario_id=usuario_id)

    eliminar(consulta_id)

    assert listar_consultas().total == 0
    with pytest.raises(ErrorDeConsulta):
        obtener_detalle(consulta_id)
    with pytest.raises(ErrorDeConsulta):
        eliminar(consulta_id)


def test_detalle_de_consulta_inexistente_falla(session: Session) -> None:
    with pytest.raises(ErrorDeConsulta) as error:
        obtener_detalle(9999)

    assert "No existe la consulta #9999" in str(error.value)


def test_opciones_de_filtro() -> None:
    assert opciones_de_filtro() == [
        {"valor": "", "texto": "Todas"},
        {"valor": "pendiente", "texto": "Pendientes"},
        {"valor": "respondida", "texto": "Respondidas"},
    ]
