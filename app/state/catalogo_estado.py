"""Estado del catalogo (T-030, T-033).

No abre sesiones ni importa el engine (T-062): le pasa los filtros a
``app.service.catalogo_servicio``, que resuelve la consulta y abre su sesion.

La carga es explicita (``cargando``) para poder mostrar skeletons en vez de
comparar listas contra ``[]``; el error se guarda como texto para la pagina y el
detalle tecnico va al log (T-064).
"""

from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Any

import reflex as rx
from sqlalchemy.exc import SQLAlchemyError

from app.service.catalogo_servicio import (
    ORDEN_POR_DEFECTO,
    categoria_desde_valor,
    listar_catalogo,
    opciones_de_filtro,
)

logger = logging.getLogger(__name__)

MENSAJE_ERROR = "No pudimos cargar el catalogo. Proba de nuevo en unos segundos."


class CatalogoEstado(rx.State):
    """Listado, filtros y paginacion del catalogo."""

    # Datos ya formateados por el servicio.
    productos: list[dict[str, Any]] = []
    categorias: list[dict[str, str]] = []
    talles: list[dict[str, str]] = []
    colores: list[dict[str, str]] = []

    # Filtros (D-014). El vacio significa "todos".
    busqueda: str = ""
    categoria: str = ""
    talle: str = ""
    color: str = ""
    orden: str = ORDEN_POR_DEFECTO

    # Paginacion de 12 por pagina (D-014).
    pagina: int = 1
    total_paginas: int = 1
    total: int = 0

    cargando: bool = True
    error: str = ""

    @rx.var
    def hay_filtros(self) -> bool:
        """True when at least one filter could remove products from the grid."""
        return bool(
            self.busqueda.strip() or self.categoria or self.talle or self.color
        )

    @rx.event
    def on_load(self):
        """Load the filter options and the first page."""
        self._cargar_opciones()
        self.pagina = 1
        self._cargar()

    @rx.event
    def set_busqueda(self, value: str) -> None:
        self.busqueda = value

    @rx.event
    def set_categoria(self, value: str) -> None:
        self.categoria = value
        self._reiniciar_y_cargar()

    @rx.event
    def set_talle(self, value: str) -> None:
        self.talle = value
        self._reiniciar_y_cargar()

    @rx.event
    def set_color(self, value: str) -> None:
        self.color = value
        self._reiniciar_y_cargar()

    @rx.event
    def set_orden(self, value: str) -> None:
        self.orden = value
        self._reiniciar_y_cargar()

    @rx.event
    def buscar(self, form_data: dict[str, Any] | None = None):
        """Apply the whole filter bar (form submit and the Buscar button).

        The selects already reload on change; reading them here too means Enter
        always applies exactly what the bar shows.
        """
        if form_data:
            for campo, atributo in (
                ("busqueda", "busqueda"),
                ("categoria", "categoria"),
                ("talle", "talle"),
                ("color", "color"),
                ("orden", "orden"),
            ):
                valor = form_data.get(campo)
                if isinstance(valor, str):
                    setattr(self, atributo, valor)
        self._reiniciar_y_cargar()

    @rx.event
    def limpiar_filtros(self):
        """Back to the unfiltered catalog, first page."""
        self.busqueda = ""
        self.categoria = ""
        self.talle = ""
        self.color = ""
        self.orden = ORDEN_POR_DEFECTO
        self._reiniciar_y_cargar()

    @rx.event
    def pagina_anterior(self):
        if self.pagina > 1:
            self.pagina -= 1
            self._cargar()

    @rx.event
    def pagina_siguiente(self):
        if self.pagina < self.total_paginas:
            self.pagina += 1
            self._cargar()

    @rx.event
    def reintentar(self):
        self._cargar()

    def _reiniciar_y_cargar(self) -> None:
        """A filter change always lands on page 1: page 4 may no longer exist."""
        self.pagina = 1
        self._cargar()

    def _cargar_opciones(self) -> None:
        try:
            opciones = opciones_de_filtro()
        except SQLAlchemyError:
            logger.exception("No se pudieron cargar las opciones del catalogo")
            return

        self.categorias = opciones.categorias
        self.talles = opciones.talles
        self.colores = opciones.colores

    def _cargar(self) -> None:
        """Query the catalog and store the result; never raises into Reflex."""
        self.cargando = True
        self.error = ""

        try:
            resultado = listar_catalogo(
                busqueda=self.busqueda,
                categoria_id=categoria_desde_valor(self.categoria),
                talle=self.talle,
                color=self.color,
                orden=self.orden,
                pagina=self.pagina,
            )
        except SQLAlchemyError:
            logger.exception("Fallo la consulta del catalogo")
            self.productos = []
            self.total = 0
            self.total_paginas = 1
            self.error = MENSAJE_ERROR
            self.cargando = False
            return

        self.productos = [asdict(producto) for producto in resultado.productos]
        self.total = resultado.total
        self.pagina = resultado.pagina
        self.total_paginas = resultado.total_paginas
        self.cargando = False
