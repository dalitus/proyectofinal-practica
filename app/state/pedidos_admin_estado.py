"""Listado y detalle de pedidos del admin (T-051, D-030).

Los filtros y la paginacion se resuelven en el servicio; aca solo se guardan las
vars que la pagina pinta. Toda accion que escribe vuelve a pedir el rol: una
sesion vencida con la pagina abierta no cambia un pedido (T-023).
"""

from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Any

import reflex as rx
from sqlalchemy.exc import SQLAlchemyError

from app.service import pedido_servicio
from app.service.pedido_servicio import ErrorDePedido
from app.state.admin_estado import AdminEstado
from app.state.parametros import id_de_la_url
from app.ui import Toast

logger = logging.getLogger(__name__)

MENSAJE_ERROR = "No pudimos cargar los pedidos. Proba de nuevo en unos segundos."
RUTA_LISTA = "/admin/pedidos"


class PedidosAdminEstado(AdminEstado):
    """Una pagina de pedidos con filtro por estado y busqueda."""

    filtro: str = ""
    busqueda: str = ""
    pagina: int = 1
    pedidos: list[dict[str, Any]] = []
    total: int = 0
    total_paginas: int = 1

    filtros: list[dict[str, str]] = pedido_servicio.opciones_de_estado()

    @rx.event
    async def on_load(self):
        """Guarda de rol y carga de la lista, sobre esta instancia (T-023)."""
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
            return "No hay pedidos con estos filtros."
        if self.total == 1:
            return "1 pedido"
        return f"{self.total} pedidos"

    @rx.event
    def filtrar(self, valor: str):
        """Change the state filter and go back to the first page."""
        self.filtro = valor
        self.pagina = 1
        self._cargar()

    @rx.event
    def escribir_busqueda(self, texto: str) -> None:
        """Keep the input controlled; the query waits for the submit."""
        self.busqueda = texto

    @rx.event
    def buscar(self, datos: dict[str, Any]):
        """Search from the form, so typing does not hit the database."""
        self.busqueda = str(datos.get("busqueda", "") or "").strip()
        self.pagina = 1
        self._cargar()

    @rx.event
    def limpiar(self):
        self.filtro = ""
        self.busqueda = ""
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
            resultado = pedido_servicio.listar_pedidos(
                estado=self.filtro,
                busqueda=self.busqueda,
                pagina=self.pagina,
            )
        except SQLAlchemyError:
            logger.exception("Fallo el listado de pedidos del admin")
            self.error = MENSAJE_ERROR
            self.cargando = False
            return

        self.pedidos = [asdict(pedido) for pedido in resultado.pedidos]
        self.total = resultado.total
        self.pagina = resultado.pagina
        self.total_paginas = resultado.total_paginas
        self.filtro = resultado.filtro_estado
        self.busqueda = resultado.busqueda
        self.cargando = False


class PedidoAdminEstado(AdminEstado):
    """Un pedido con sus lineas y las transiciones que el ciclo permite."""

    pedido_id: int = 0
    pedido: dict[str, Any] = {}
    lineas: list[dict[str, Any]] = []
    siguientes: list[dict[str, str]] = []
    no_encontrado: bool = False

    @rx.event
    async def on_load(self):
        """Guarda de rol y carga del detalle, sobre esta instancia (T-023)."""
        return await self._iniciar()

    @rx.event
    async def reintentar(self):
        return await self._iniciar()

    @rx.var
    def titulo(self) -> str:
        return f"Pedido #{self.pedido_id}" if self.pedido_id else "Pedido"

    @rx.var
    def puede_cambiar(self) -> bool:
        return bool(self.siguientes) and not self.no_encontrado

    @rx.var
    def unidades_texto(self) -> str:
        """One unit is singular: the total is shown under the lines."""
        total = int(self.pedido.get("unidades", 0) or 0)
        return "1 unidad" if total == 1 else f"{total} unidades"

    def _cargar(self) -> None:
        self.no_encontrado = False
        self.pedido = {}
        self.lineas = []
        self.siguientes = []

        pedido_id = id_de_la_url(self.router.url)
        if pedido_id is None:
            self._marcar_no_encontrado()
            return

        try:
            detalle = pedido_servicio.obtener_detalle(pedido_id)
        except ErrorDePedido:
            self._marcar_no_encontrado()
            return
        except SQLAlchemyError:
            logger.exception("Fallo la consulta del pedido %s", pedido_id)
            self.error = MENSAJE_ERROR
            self.cargando = False
            return

        self.pedido_id = detalle.id
        self.pedido = asdict(detalle)
        self.lineas = [asdict(linea) for linea in detalle.lineas]
        self.siguientes = pedido_servicio.estados_siguientes(detalle.estado)
        self.cargando = False

    @rx.event
    async def cambiar(self, nuevo: str):
        """Apply one transition after the confirmation dialog (D-010)."""
        destino = await self._exigir_admin()
        if destino is not None:
            return destino

        try:
            pedido_servicio.cambiar_estado(
                self.pedido_id,
                nuevo,
                admin_id=self.admin_id,
            )
        except ErrorDePedido as error:
            # Otro admin pudo moverlo: se recarga para mostrar el estado real.
            self._cargar()
            return Toast(str(error), tone="error")
        except SQLAlchemyError:
            logger.exception("Fallo el cambio de estado del pedido %s", self.pedido_id)
            self.error = MENSAJE_ERROR
            return Toast(MENSAJE_ERROR, tone="error")

        self._cargar()
        return Toast(
            f"Pedido #{self.pedido_id}: {pedido_servicio.etiqueta_de_estado(nuevo).lower()}"
        )

    def _marcar_no_encontrado(self) -> None:
        self.no_encontrado = True
        self.cargando = False
        self.pedido = {}
        self.lineas = []
        self.siguientes = []
