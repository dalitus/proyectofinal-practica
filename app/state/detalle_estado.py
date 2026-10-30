"""Estado del detalle de producto (T-031).

La ruta es ``/producto/[producto_id]`` (D-024) y el id se lee del router, no de
una variable en memoria: recargar o abrir el link directo tiene que funcionar.

Como en el catalogo, este estado no abre sesiones ni importa el engine (T-062) y
el error se guarda como texto; el detalle tecnico va al log (T-064).

La seleccion de color y talle se resuelve en Python y la pagina solo pinta:
comparar cantidades dentro de la vista falla porque el item de ``rx.foreach``
llega como ``Var[Any]``.
"""

from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Any

import reflex as rx
from sqlalchemy.exc import SQLAlchemyError

from app.service.catalogo_servicio import (
    estado_de_stock,
    obtener_detalle,
    talles_por_color,
)

logger = logging.getLogger(__name__)

MENSAJE_ERROR = "No pudimos cargar el producto. Proba de nuevo en unos segundos."


def _id_de_la_ruta(valor: Any) -> int | None:
    """Turn the route parameter into a product id; ``None`` when it is not one."""
    if isinstance(valor, list):
        valor = valor[0] if valor else ""
    try:
        return int(str(valor).strip())
    except (TypeError, ValueError):
        return None


class DetalleEstado(rx.State):
    """Producto, variantes y seleccion de color/talle del detalle."""

    # Datos ya formateados por el servicio.
    producto: dict[str, Any] = {}
    talles_por_color: dict[str, list[dict[str, Any]]] = {}

    # Seleccion actual. El vacio significa "todavia sin elegir".
    color: str = ""
    talle: str = ""

    cargando: bool = True
    no_encontrado: bool = False
    error: str = ""

    @rx.var
    def talles_del_color(self) -> list[dict[str, Any]]:
        """Sizes to render for the chosen colour, with their availability."""
        return self.talles_por_color.get(self.color, [])

    @rx.var
    def nombre(self) -> str:
        """Page title, falling back to the generic one while loading."""
        return str(self.producto.get("nombre", "")) or "Producto"

    @rx.var
    def colores(self) -> list[str]:
        """Colour picker options, typed so ``rx.foreach`` can iterate them."""
        return list(self.producto.get("colores", []))

    @rx.var
    def cantidad_seleccionada(self) -> int:
        """Units left for the chosen (colour, size) pair."""
        for variante in self.producto.get("variantes", []):
            if variante["color"] == self.color and variante["talle"] == self.talle:
                return int(variante["cantidad"])
        return 0

    @rx.var
    def variante_id(self) -> int:
        """``stocks`` id of the chosen pair: the cart stores variants, not products."""
        for variante in self.producto.get("variantes", []):
            if variante["color"] == self.color and variante["talle"] == self.talle:
                return int(variante["id"])
        return 0

    @rx.var
    def stock_estado(self) -> str:
        return estado_de_stock(self.cantidad_seleccionada)[0]

    @rx.var
    def stock_etiqueta(self) -> str:
        return estado_de_stock(self.cantidad_seleccionada)[1]

    @rx.var
    def puede_comprar(self) -> bool:
        return self.cantidad_seleccionada > 0

    @rx.event
    def on_load(self):
        """Load the product named by the route; never raises into Reflex."""
        self.cargando = True
        self.error = ""
        self.no_encontrado = False
        self.producto = {}
        self.talles_por_color = {}
        self.color = ""
        self.talle = ""

        producto_id = _id_de_la_ruta(self.router.page.params.get("producto_id"))
        if producto_id is None:
            self._marcar_no_encontrado()
            return

        try:
            detalle = obtener_detalle(producto_id)
        except SQLAlchemyError:
            logger.exception("Fallo la consulta del detalle de producto")
            self.error = MENSAJE_ERROR
            self.cargando = False
            return

        if detalle is None:
            self._marcar_no_encontrado()
            return

        self.producto = asdict(detalle)
        self.talles_por_color = talles_por_color(detalle)
        self.cargando = False
        self._elegir_inicial()

    @rx.event
    def elegir_color(self, color: str) -> None:
        """Switch colour and keep a size that exists in that colour.

        The preferred size is the one already selected if it has stock; if not,
        the first size with stock; if the whole colour is sold out, the same size
        so the badge can say "sin stock" instead of silently jumping.
        """
        if color not in self.talles_por_color:
            return

        self.color = color
        talles = self.talles_por_color[color]

        if self._esta_disponible(talles, self.talle):
            return

        self.talle = (
            self._primer_disponible(talles)
            or (self.talle if any(t["talle"] == self.talle for t in talles) else "")
            or (talles[0]["talle"] if talles else "")
        )

    @rx.event
    def elegir_talle(self, talle: str) -> None:
        self.talle = talle

    @rx.event
    def reintentar(self):
        self.on_load()

    def _marcar_no_encontrado(self) -> None:
        self.no_encontrado = True
        self.cargando = False
        self.producto = {}
        self.talles_por_color = {}

    def _elegir_inicial(self) -> None:
        """Start on the first colour that has stock, on a size that has stock."""
        colores = list(self.talles_por_color)
        if not colores:
            return

        for color in colores:
            talles = self.talles_por_color[color]
            disponible = self._primer_disponible(talles)
            if disponible:
                self.color = color
                self.talle = disponible
                return

        # Everything is sold out: still show the product with "sin stock".
        self.color = colores[0]
        talles = self.talles_por_color[colores[0]]
        self.talle = talles[0]["talle"] if talles else ""

    @staticmethod
    def _primer_disponible(talles: list[dict[str, Any]]) -> str:
        for talle in talles:
            if not talle["agotado"]:
                return str(talle["talle"])
        return ""

    @staticmethod
    def _esta_disponible(talles: list[dict[str, Any]], talle: str) -> bool:
        return any(item["talle"] == talle and not item["agotado"] for item in talles)
