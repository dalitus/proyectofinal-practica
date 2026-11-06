"""Historial y detalle de pedidos del comprador (T-076, D-002, D-030).

El comprador ve solo sus pedidos: el ``usuario_id`` sale del token y la consulta
filtra por el en SQL. Un pedido ajeno se trata como inexistente, no como un
error de permisos, para no confirmar ids de otros.
"""

from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Any

import reflex as rx
from sqlalchemy.exc import SQLAlchemyError

from app.service import pedido_servicio
from app.service.pedido_servicio import ErrorDePedido
from app.state.comprador_estado import CompradorEstado
from app.state.parametros import id_de_la_url

logger = logging.getLogger(__name__)

MENSAJE_CARGA = "No pudimos cargar tus pedidos. Proba de nuevo en unos segundos."


class MisPedidosEstado(CompradorEstado):
    """Una pagina del historial propio, con paginacion."""

    pedidos: list[dict[str, Any]] = []
    total: int = 0
    pagina: int = 1
    total_paginas: int = 1

    @rx.event
    async def on_load(self):
        """Guarda de sesion y carga del historial (T-076)."""
        return await self._iniciar()

    @rx.event
    async def reintentar(self):
        return await self._iniciar()

    @rx.var
    def vacio(self) -> bool:
        return not self.pedidos

    @rx.var
    def hay_anterior(self) -> bool:
        return self.pagina > 1

    @rx.var
    def hay_siguiente(self) -> bool:
        return self.pagina < self.total_paginas

    @rx.var
    def resumen(self) -> str:
        if self.total == 0:
            return "Todavia no hiciste pedidos."
        if self.total == 1:
            return "1 pedido"
        return f"{self.total} pedidos"

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
            resultado = pedido_servicio.listar_mis_pedidos(
                self.usuario_id,
                pagina=self.pagina,
            )
        except ErrorDePedido as error:
            self.error = str(error)
            self.cargando = False
            return
        except SQLAlchemyError:
            logger.exception("Fallo el listado de pedidos del usuario %s", self.usuario_id)
            self.error = MENSAJE_CARGA
            self.cargando = False
            return

        self.pedidos = [asdict(pedido) for pedido in resultado.pedidos]
        self.total = resultado.total
        self.pagina = resultado.pagina
        self.total_paginas = resultado.total_paginas
        self.cargando = False


class MiPedidoEstado(CompradorEstado):
    """Un pedido propio con sus lineas y el envio."""

    pedido_id: int = 0
    pedido: dict[str, Any] = {}
    lineas: list[dict[str, Any]] = []
    no_encontrado: bool = False

    @rx.event
    async def on_load(self):
        """Guarda de sesion y carga del detalle (T-076)."""
        return await self._iniciar()

    @rx.event
    async def reintentar(self):
        return await self._iniciar()

    @rx.var
    def titulo(self) -> str:
        return f"Pedido #{self.pedido_id}" if self.pedido_id else "Pedido"

    @rx.var
    def unidades_texto(self) -> str:
        total = int(self.pedido.get("unidades", 0) or 0)
        return "1 unidad" if total == 1 else f"{total} unidades"

    def _cargar(self) -> None:
        self.no_encontrado = False
        self.pedido = {}
        self.lineas = []

        pedido_id = id_de_la_url(self.router.url)
        if pedido_id is None:
            self.pedido_id = 0
            self._marcar_no_encontrado()
            return

        self.pedido_id = pedido_id
        try:
            detalle = pedido_servicio.obtener_mi_pedido(pedido_id, self.usuario_id)
        except ErrorDePedido:
            self._marcar_no_encontrado()
            return
        except SQLAlchemyError:
            logger.exception("Fallo la consulta del pedido %s", pedido_id)
            self.error = MENSAJE_CARGA
            self.cargando = False
            return

        self.pedido_id = detalle.id
        self.pedido = asdict(detalle)
        self.lineas = [asdict(linea) for linea in detalle.lineas]
        self.cargando = False

    def _marcar_no_encontrado(self) -> None:
        self.no_encontrado = True
        self.cargando = False
        self.pedido = {}
        self.lineas = []
