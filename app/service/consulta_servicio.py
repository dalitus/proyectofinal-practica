"""Consultas: listado, respuesta y borrado desde el admin (T-052, D-019, D-030).

The admin answers from the panel and the buyer reads the answer on the web; there
is no email (D-030). The filter and the pagination live here so the page only
renders. Each function opens its own session through the repository (D-033).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime

from app.model.consulta_model import Consulta
from app.model.perfil_modelo import UserProfile
from app.repository import consulta_repositorio
from app.repository.consulta_repositorio import (
    ConsultaNoEncontrada,
    ConsultaYaRespondida,
)
from app.service.auditoria import registrar as registrar_auditoria


class ErrorDeConsulta(ValueError):
    """Missing question, empty answer or a question that was already answered."""


CONSULTAS_POR_PAGINA = 10
MAXIMO_RESPUESTA = 2000
MAXIMO_ASUNTO = 120
MAXIMO_MENSAJE = 2000
LARGO_DEL_RESUMEN = 140

# Filtro del panel: valor del select -> etiqueta.
FILTROS_DE_CONSULTA: dict[str, str] = {
    "": "Todas",
    "pendiente": "Pendientes",
    "respondida": "Respondidas",
}

ETIQUETAS_DE_CONSULTA: dict[str, str] = {
    "pendiente": "Pendiente",
    "respondida": "Respondida",
}


@dataclass(frozen=True)
class ConsultaEnLista:
    """One row of the admin inbox, ready to render."""

    id: int
    asunto: str
    resumen: str
    cliente: str
    email: str
    fecha: str
    estado: str
    estado_etiqueta: str
    respondida_por: str


@dataclass(frozen=True)
class PaginaDeConsultas:
    consultas: list[ConsultaEnLista]
    total: int
    pagina: int
    total_paginas: int
    filtro: str

    @property
    def hay_anterior(self) -> bool:
        return self.pagina > 1

    @property
    def hay_siguiente(self) -> bool:
        return self.pagina < self.total_paginas


@dataclass(frozen=True)
class DetalleDeConsulta:
    id: int
    asunto: str
    mensaje: str
    cliente: str
    email: str
    fecha: str
    respuesta: str
    respondida_por: str
    fecha_respuesta: str
    estado: str
    estado_etiqueta: str


@dataclass(frozen=True)
class MiConsulta:
    """One question of the buyer's own history, ready to render (T-065)."""

    id: int
    asunto: str
    mensaje: str
    fecha: str
    estado: str
    estado_etiqueta: str
    respuesta: str
    respondida_por: str
    fecha_respuesta: str


@dataclass(frozen=True)
class PaginaDeMisConsultas:
    consultas: list[MiConsulta]
    total: int
    pagina: int
    total_paginas: int

    @property
    def hay_anterior(self) -> bool:
        return self.pagina > 1

    @property
    def hay_siguiente(self) -> bool:
        return self.pagina < self.total_paginas


def opciones_de_filtro() -> list[dict[str, str]]:
    """Options for the filter select, in display order."""
    return [
        {"valor": valor, "texto": texto}
        for valor, texto in FILTROS_DE_CONSULTA.items()
    ]


def normalizar_filtro(filtro: str | None) -> str:
    """Ignore an unknown filter instead of failing on a stale link."""
    return filtro if filtro in FILTROS_DE_CONSULTA else ""


def estado_de_consulta(consulta: Consulta) -> str:
    """A question is answered as soon as it has a non-empty answer."""
    return "respondida" if (consulta.respuesta or "").strip() else "pendiente"


def etiqueta_de_consulta(estado: str) -> str:
    return ETIQUETAS_DE_CONSULTA.get(estado, estado)


def _fecha(momento: datetime | None) -> str:
    return momento.strftime("%d/%m/%Y %H:%M") if momento else ""


def _resumen(mensaje: str) -> str:
    texto = " ".join((mensaje or "").split())
    if len(texto) <= LARGO_DEL_RESUMEN:
        return texto
    return f"{texto[:LARGO_DEL_RESUMEN].rstrip()}..."


def _persona(perfil: UserProfile | None, usuario_id: int | None) -> tuple[str, str]:
    """Return (display name, email) for a profile that may be missing."""
    if perfil is None:
        if usuario_id:
            return f"Usuario #{usuario_id}", ""
        return "Cuenta eliminada", ""
    nombre = f"{perfil.nombre} {perfil.apellido}".strip()
    return nombre or perfil.email, perfil.email


def _a_consulta_en_lista(
    consulta: Consulta,
    comprador: UserProfile | None,
    administrador: UserProfile | None,
) -> ConsultaEnLista:
    estado = estado_de_consulta(consulta)
    cliente, email = _persona(comprador, consulta.usuario_id)
    respondida_por, _ = _persona(administrador, consulta.respondido_por_id)

    return ConsultaEnLista(
        id=consulta.id_consulta or 0,
        asunto=consulta.asunto,
        resumen=_resumen(consulta.mensaje),
        cliente=cliente,
        email=email,
        fecha=_fecha(consulta.fecha_creacion),
        estado=estado,
        estado_etiqueta=etiqueta_de_consulta(estado),
        respondida_por=respondida_por if estado == "respondida" else "",
    )


def _a_mi_consulta(consulta: Consulta, administrador: UserProfile | None) -> MiConsulta:
    """One buyer row: the answer is shown only when it exists (T-065)."""
    estado = estado_de_consulta(consulta)
    respondida_por, _ = _persona(administrador, consulta.respondido_por_id)

    return MiConsulta(
        id=consulta.id_consulta or 0,
        asunto=consulta.asunto,
        mensaje=consulta.mensaje,
        fecha=_fecha(consulta.fecha_creacion),
        estado=estado,
        estado_etiqueta=etiqueta_de_consulta(estado),
        respuesta=consulta.respuesta or "",
        respondida_por=respondida_por,
        fecha_respuesta=_fecha(consulta.fecha_respuesta),
    )


def listar_consultas(*, filtro: str = "", pagina: int = 1) -> PaginaDeConsultas:
    """One page of questions with the pending/answered filter applied in SQL."""
    estado = normalizar_filtro(filtro)
    total = consulta_repositorio.contar_consultas(estado=estado)
    total_paginas = max(1, math.ceil(total / CONSULTAS_POR_PAGINA))
    actual = min(max(1, int(pagina or 1)), total_paginas)

    filas = consulta_repositorio.listar_consultas(
        estado=estado,
        offset=(actual - 1) * CONSULTAS_POR_PAGINA,
        limite=CONSULTAS_POR_PAGINA,
    )

    return PaginaDeConsultas(
        consultas=[_a_consulta_en_lista(*fila) for fila in filas],
        total=total,
        pagina=actual,
        total_paginas=total_paginas,
        filtro=estado,
    )


def obtener_detalle(consulta_id: int) -> DetalleDeConsulta:
    """Full question with the answer and both names."""
    fila = consulta_repositorio.obtener_consulta(consulta_id)
    if fila is None:
        raise ErrorDeConsulta(f"No existe la consulta #{consulta_id}.")

    consulta, comprador, administrador = fila
    cliente, email = _persona(comprador, consulta.usuario_id)
    respondida_por, _ = _persona(administrador, consulta.respondido_por_id)
    estado = estado_de_consulta(consulta)

    return DetalleDeConsulta(
        id=consulta.id_consulta or 0,
        asunto=consulta.asunto,
        mensaje=consulta.mensaje,
        cliente=cliente,
        email=email,
        fecha=_fecha(consulta.fecha_creacion),
        respuesta=consulta.respuesta or "",
        respondida_por=respondida_por,
        fecha_respuesta=_fecha(consulta.fecha_respuesta),
        estado=estado,
        estado_etiqueta=etiqueta_de_consulta(estado),
    )


def listar_mis_consultas(
    usuario_id: int,
    *,
    pagina: int = 1,
) -> PaginaDeMisConsultas:
    """One page of the buyer's own questions, scoped by the session id (T-065)."""
    if usuario_id <= 0:
        raise ErrorDeConsulta("Necesitas iniciar sesion para ver tus consultas.")

    total = consulta_repositorio.contar_consultas_de_usuario(usuario_id=usuario_id)
    total_paginas = max(1, math.ceil(total / CONSULTAS_POR_PAGINA))
    actual = min(max(1, int(pagina or 1)), total_paginas)

    filas = consulta_repositorio.listar_consultas_de_usuario(
        usuario_id,
        offset=(actual - 1) * CONSULTAS_POR_PAGINA,
        limite=CONSULTAS_POR_PAGINA,
    )

    return PaginaDeMisConsultas(
        consultas=[_a_mi_consulta(consulta, admin) for consulta, admin in filas],
        total=total,
        pagina=actual,
        total_paginas=total_paginas,
    )


def crear(usuario_id: int, asunto: str, mensaje: str) -> int:
    """Validate and store the buyer's question; return the new id (T-065).

    The author is the id resolved from the session token, so an anonymous call
    is impossible and the form cannot post on behalf of someone else (D-002).
    """
    if usuario_id <= 0:
        raise ErrorDeConsulta("Necesitas iniciar sesion para enviar una consulta.")

    titulo = (asunto or "").strip()
    texto = (mensaje or "").strip()

    if not titulo:
        raise ErrorDeConsulta("Escribi un asunto.")
    if len(titulo) > MAXIMO_ASUNTO:
        raise ErrorDeConsulta(
            f"El asunto no puede superar los {MAXIMO_ASUNTO} caracteres."
        )
    if not texto:
        raise ErrorDeConsulta("Escribi tu consulta.")
    if len(texto) > MAXIMO_MENSAJE:
        raise ErrorDeConsulta(
            f"La consulta no puede superar los {MAXIMO_MENSAJE} caracteres."
        )

    consulta_id = consulta_repositorio.crear_consulta(
        usuario_id=usuario_id,
        asunto=titulo,
        mensaje=texto,
        ahora=datetime.now(),
    )

    return consulta_id


def responder(consulta_id: int, respuesta: str, admin_id: int) -> str:
    """Validate and store the answer; return the stored text."""
    texto = (respuesta or "").strip()
    if not texto:
        raise ErrorDeConsulta("Escribi una respuesta.")
    if len(texto) > MAXIMO_RESPUESTA:
        raise ErrorDeConsulta(
            f"La respuesta no puede superar los {MAXIMO_RESPUESTA} caracteres."
        )

    try:
        consulta_repositorio.responder(
            consulta_id=consulta_id,
            respuesta=texto,
            admin_id=admin_id,
            ahora=datetime.now(),
        )
    except ConsultaNoEncontrada as error:
        raise ErrorDeConsulta(f"No existe la consulta #{consulta_id}.") from error
    except ConsultaYaRespondida as error:
        raise ErrorDeConsulta(
            "Esa consulta ya tiene respuesta. Recarga la lista."
        ) from error

    registrar_auditoria(
        accion="responder_consulta",
        entidad="consulta",
        entidad_id=consulta_id,
        admin_id=admin_id,
        detalle=f"{len(texto)} caracteres",
    )

    return texto


def eliminar(consulta_id: int, *, admin_id: int | None = None) -> None:
    """Delete the question; the page asks for confirmation first (D-030)."""
    try:
        consulta_repositorio.eliminar(consulta_id)
    except ConsultaNoEncontrada as error:
        raise ErrorDeConsulta(f"No existe la consulta #{consulta_id}.") from error

    registrar_auditoria(
        accion="eliminar_consulta",
        entidad="consulta",
        entidad_id=consulta_id,
        admin_id=admin_id,
    )
