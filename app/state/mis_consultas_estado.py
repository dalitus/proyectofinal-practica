"""Consultas del comprador en ``/consultas`` (T-065, D-002).

El comprador escribe su consulta y lee la respuesta en la web (D-030). El autor
sale del token de ``LocalAuthState``: el formulario nunca manda un ``usuario_id``,
asi que no se puede escribir a nombre de otra persona (D-002). Un invitado va al
login con la ruta de vuelta, y la lista solo trae las filas del dueno.

El estado no abre sesiones ni importa el engine (T-062): valida lo que se puede
validar sin base, pide el resto al servicio y manda el detalle tecnico al log.
"""

from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Any

import reflex as rx
from reflex_local_auth.local_auth import LocalAuthState
from sqlalchemy.exc import SQLAlchemyError

from app.service import consulta_servicio
from app.service.consulta_servicio import (
    MAXIMO_ASUNTO,
    MAXIMO_MENSAJE,
    ErrorDeConsulta,
)
from app.service.sesion_servicio import usuario_con_rol
from app.state.parametros import ruta_interna
from app.ui import Toast

logger = logging.getLogger(__name__)

MENSAJE_CARGA = "No pudimos cargar tus consultas. Proba de nuevo en unos segundos."
MENSAJE_ENVIO = "No pudimos enviar la consulta. Proba de nuevo en unos segundos."

RUTA_LOGIN = "/login?next="
RUTA_CONSULTAS = "/consultas"


class MisConsultasEstado(rx.State):
    """Historial propio y alta de consultas del comprador conectado."""

    autorizado: bool = False
    cargando: bool = True
    error: str = ""
    usuario_id: int = 0

    consultas: list[dict[str, Any]] = []
    total: int = 0
    pagina: int = 1
    total_paginas: int = 1

    # Formulario controlado: un error no borra lo escrito ni lo enviado.
    asunto: str = ""
    mensaje: str = ""
    error_asunto: str = ""
    error_mensaje: str = ""
    enviando: bool = False

    ASUNTO_MAXIMO = MAXIMO_ASUNTO
    MENSAJE_MAXIMO = MAXIMO_MENSAJE

    @rx.event
    async def on_load(self):
        """Guarda de sesion y carga del historial (T-023, T-065)."""
        return await self._iniciar()

    @rx.event
    async def reintentar(self):
        return await self._iniciar()

    @rx.var
    def vacio(self) -> bool:
        return not self.consultas

    @rx.var
    def hay_anterior(self) -> bool:
        return self.pagina > 1

    @rx.var
    def hay_siguiente(self) -> bool:
        return self.pagina < self.total_paginas

    @rx.var
    def resumen(self) -> str:
        if self.total == 0:
            return "Todavia no hiciste consultas."
        if self.total == 1:
            return "1 consulta"
        return f"{self.total} consultas"

    @rx.event
    def escribir_asunto(self, texto: str) -> None:
        self.asunto = texto
        self.error_asunto = ""

    @rx.event
    def escribir_mensaje(self, texto: str) -> None:
        self.mensaje = texto
        self.error_mensaje = ""

    @rx.event
    def anterior(self):
        if self.pagina > 1:
            self.pagina -= 1
            self._cargar()

    @rx.event
    def siguiente(self):
        if self.pagina < self.total_paginas:
            self.pagina += 1
            self._cargar()

    @rx.event
    async def enviar(self, datos: dict[str, Any]):
        """Validate, store and reload; the field error stays next to the field."""
        destino = await self._exigir_sesion()
        if destino is not None:
            return destino

        asunto = str(datos.get("asunto", self.asunto) or "").strip()
        mensaje = str(datos.get("mensaje", self.mensaje) or "").strip()
        self.asunto = asunto
        self.mensaje = mensaje

        if not self._validar(asunto, mensaje):
            return None

        self.enviando = True
        try:
            consulta_servicio.crear(self.usuario_id, asunto, mensaje)
        except ErrorDeConsulta as error:
            self.enviando = False
            self.error_mensaje = str(error)
            return None
        except SQLAlchemyError:
            logger.exception("Fallo el alta de la consulta")
            self.enviando = False
            self.error = MENSAJE_ENVIO
            return Toast(MENSAJE_ENVIO, tone="error")

        self.enviando = False
        self.asunto = ""
        self.mensaje = ""
        self.error_asunto = ""
        self.error_mensaje = ""
        self.pagina = 1
        self._cargar()
        return Toast("Consulta enviada")

    def _validar(self, asunto: str, mensaje: str) -> bool:
        """Field checks that do not need the database (design.md 5)."""
        self.error_asunto = ""
        self.error_mensaje = ""

        if not asunto:
            self.error_asunto = "Escribi un asunto."
        elif len(asunto) > MAXIMO_ASUNTO:
            self.error_asunto = (
                f"El asunto no puede superar los {MAXIMO_ASUNTO} caracteres."
            )

        if not mensaje:
            self.error_mensaje = "Escribi tu consulta."
        elif len(mensaje) > MAXIMO_MENSAJE:
            self.error_mensaje = (
                f"La consulta no puede superar los {MAXIMO_MENSAJE} caracteres."
            )

        return not self.error_asunto and not self.error_mensaje

    async def _iniciar(self):
        """Resolve the session and load the list, or redirect to the login."""
        self.cargando = True
        self.error = ""
        self.autorizado = False

        destino = await self._exigir_sesion()
        if destino is not None:
            return destino

        self._cargar()
        return None

    async def _exigir_sesion(self):
        """Return a redirect for a guest, or ``None`` with the user id set."""
        auth = await self.get_state(LocalAuthState)
        usuario_id = usuario_con_rol(auth.auth_token)
        if usuario_id is None:
            return rx.redirect(RUTA_LOGIN + ruta_interna(self.router.url, RUTA_CONSULTAS))

        self.usuario_id = usuario_id
        self.autorizado = True
        return None

    def _cargar(self) -> None:
        try:
            resultado = consulta_servicio.listar_mis_consultas(
                self.usuario_id,
                pagina=self.pagina,
            )
        except ErrorDeConsulta as error:
            self.error = str(error)
            self.cargando = False
            return
        except SQLAlchemyError:
            logger.exception("Fallo el listado de consultas del usuario %s", self.usuario_id)
            self.error = MENSAJE_CARGA
            self.cargando = False
            return

        self.consultas = [asdict(consulta) for consulta in resultado.consultas]
        self.total = resultado.total
        self.pagina = resultado.pagina
        self.total_paginas = resultado.total_paginas
        self.cargando = False
