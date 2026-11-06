"""Bandeja de consultas y respuesta del admin (T-052, D-030).

El filtro pendiente/respondida y la paginacion los resuelve el servicio. La
respuesta se guarda con el id del admin que la escribe y queda auditada (T-053);
nunca se envia por correo (D-030).
"""

from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Any

import reflex as rx
from sqlalchemy.exc import SQLAlchemyError

from app.service import consulta_servicio
from app.service.consulta_servicio import MAXIMO_RESPUESTA, ErrorDeConsulta
from app.state.admin_estado import AdminEstado
from app.state.parametros import id_de_la_url
from app.ui import Toast

logger = logging.getLogger(__name__)

MENSAJE_ERROR = "No pudimos cargar las consultas. Proba de nuevo en unos segundos."
RUTA_LISTA = "/admin/consultas"


class ConsultasAdminEstado(AdminEstado):
    """Una pagina de consultas con filtro por estado."""

    filtro: str = ""
    pagina: int = 1
    consultas: list[dict[str, Any]] = []
    total: int = 0
    total_paginas: int = 1

    filtros: list[dict[str, str]] = consulta_servicio.opciones_de_filtro()

    @rx.event
    async def on_load(self):
        """Guarda de rol y carga de la bandeja, sobre esta instancia (T-023)."""
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
            return "No hay consultas con este filtro."
        if self.total == 1:
            return "1 consulta"
        return f"{self.total} consultas"

    @rx.event
    def filtrar(self, valor: str):
        self.filtro = valor
        self.pagina = 1
        self._cargar()

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

    def _cargar(self) -> None:
        try:
            resultado = consulta_servicio.listar_consultas(
                filtro=self.filtro,
                pagina=self.pagina,
            )
        except SQLAlchemyError:
            logger.exception("Fallo el listado de consultas del admin")
            self.error = MENSAJE_ERROR
            self.cargando = False
            return

        self.consultas = [asdict(consulta) for consulta in resultado.consultas]
        self.total = resultado.total
        self.pagina = resultado.pagina
        self.total_paginas = resultado.total_paginas
        self.filtro = resultado.filtro
        self.cargando = False


class ConsultaAdminEstado(AdminEstado):
    """Una consulta con su mensaje, la respuesta y el borrado."""

    consulta_id: int = 0
    consulta: dict[str, Any] = {}
    borrador: str = ""
    error_borrador: str = ""
    enviando: bool = False
    no_encontrada: bool = False

    MAXIMO = MAXIMO_RESPUESTA

    @rx.event
    async def on_load(self):
        """Guarda de rol y carga de la consulta, sobre esta instancia (T-023)."""
        return await self._iniciar()

    @rx.event
    async def reintentar(self):
        return await self._iniciar()

    @rx.var
    def titulo(self) -> str:
        return f"Consulta #{self.consulta_id}" if self.consulta_id else "Consulta"

    @rx.var
    def pendiente(self) -> bool:
        return self.consulta.get("estado") == "pendiente"

    def _cargar(self) -> None:
        self.no_encontrada = False
        self.consulta = {}
        self.borrador = ""
        self.error_borrador = ""

        consulta_id = id_de_la_url(self.router.url)
        if consulta_id is None:
            self._marcar_no_encontrada()
            return

        try:
            detalle = consulta_servicio.obtener_detalle(consulta_id)
        except ErrorDeConsulta:
            self._marcar_no_encontrada()
            return
        except SQLAlchemyError:
            logger.exception("Fallo la consulta de la consulta %s", consulta_id)
            self.error = MENSAJE_ERROR
            self.cargando = False
            return

        self.consulta_id = detalle.id
        self.consulta = asdict(detalle)
        self.cargando = False

    @rx.event
    def escribir(self, texto: str) -> None:
        self.borrador = texto
        self.error_borrador = ""

    @rx.event
    async def responder(self, datos: dict[str, Any]):
        """Store the answer; the field error stays next to the textarea."""
        destino = await self._exigir_admin()
        if destino is not None:
            return destino

        texto = str(datos.get("respuesta", self.borrador) or "").strip()
        self.enviando = True

        try:
            consulta_servicio.responder(self.consulta_id, texto, self.admin_id)
        except ErrorDeConsulta as error:
            self.enviando = False
            self.error_borrador = str(error)
            return None
        except SQLAlchemyError:
            logger.exception("Fallo la respuesta de la consulta %s", self.consulta_id)
            self.enviando = False
            self.error_borrador = MENSAJE_ERROR
            return None

        self.enviando = False
        self._cargar()
        return Toast("Respuesta guardada")

    @rx.event
    async def eliminar(self):
        """Delete the question after the confirmation dialog (D-030)."""
        destino = await self._exigir_admin()
        if destino is not None:
            return destino

        try:
            consulta_servicio.eliminar(self.consulta_id, admin_id=self.admin_id)
        except ErrorDeConsulta as error:
            return Toast(str(error), tone="error")
        except SQLAlchemyError:
            logger.exception("Fallo el borrado de la consulta %s", self.consulta_id)
            return Toast(MENSAJE_ERROR, tone="error")

        return rx.redirect(RUTA_LISTA)

    def _marcar_no_encontrada(self) -> None:
        self.no_encontrada = True
        self.cargando = False
        self.consulta = {}
