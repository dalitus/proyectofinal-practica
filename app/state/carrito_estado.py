"""Estado del carrito (T-040).

El carrito vive en la base y es del usuario de la sesion (D-002, D-008): este
estado resuelve el id desde el token de ``LocalAuthState`` con
``sesion_servicio`` y le pasa ese id al servicio. El id nunca viaja como var del
cliente, asi que editar una var en el navegador no da acceso a otro carrito.

No abre sesiones ni importa el engine (T-062); el error se guarda como texto y el
detalle tecnico va al log (T-064).
"""

from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Any, Callable

import reflex as rx
from reflex_local_auth.local_auth import LocalAuthState
from sqlalchemy.exc import SQLAlchemyError

from app.service import carrito_servicio
from app.service.carrito_servicio import CarritoDeCompra, ErrorDeCarrito
from app.service.sesion_servicio import usuario_autenticado
from app.ui import Toast

logger = logging.getLogger(__name__)

MENSAJE_ERROR = "No pudimos actualizar el carrito. Proba de nuevo en unos segundos."
RUTA_CARRITO = "/carrito"
RUTA_LOGIN = "/login?next="

Operacion = Callable[[int], CarritoDeCompra]


class CarritoEstado(rx.State):
    """Lineas del comprador, totales y las acciones del carrito."""

    # Datos ya formateados por el servicio.
    lineas: list[dict[str, Any]] = []
    total_unidades: int = 0
    subtotal: str = ""

    cargando: bool = True
    error: str = ""

    @rx.var
    def vacio(self) -> bool:
        return not self.lineas

    @rx.var
    def resumen(self) -> str:
        """Short line for the page header and the screen reader."""
        total = self.total_unidades
        if total == 0:
            return "Todavia no agregaste productos."
        if total == 1:
            return "1 producto en el carrito."
        return f"{total} productos en el carrito."

    @rx.event
    async def on_load(self):
        """Load the cart of the signed-in buyer; guests go to the login (D-002)."""
        self.cargando = True
        self.error = ""

        usuario_id = await self._usuario()
        if usuario_id is None:
            self._limpiar_vars()
            return rx.redirect(RUTA_LOGIN + RUTA_CARRITO)

        self._cargar(usuario_id)

    @rx.event
    async def agregar(self, variante_id: int, cantidad: int = 1):
        """Add units from the product detail; a guest returns here after login."""
        usuario_id = await self._usuario()
        if usuario_id is None:
            return rx.redirect(RUTA_LOGIN + self._ruta_actual())

        resultado = self._ejecutar(
            lambda usuario: carrito_servicio.agregar(usuario, variante_id, cantidad),
            usuario_id,
        )
        if resultado is not None:
            return resultado
        return Toast("Agregado al carrito")

    @rx.event
    async def sumar(self, linea_id: int):
        """One more unit, never past the variant's stock (D-022)."""
        actual = self._cantidad(linea_id)
        if actual is None:
            return None
        return await self._cambiar(linea_id, actual + 1)

    @rx.event
    async def restar(self, linea_id: int):
        """One less unit; from one unit down it removes the line."""
        actual = self._cantidad(linea_id)
        if actual is None:
            return None
        if actual <= 1:
            return await self.quitar(linea_id)
        return await self._cambiar(linea_id, actual - 1)

    @rx.event
    async def quitar(self, linea_id: int):
        """Remove a line."""
        return await self._aplicar(
            lambda usuario: carrito_servicio.quitar(usuario, linea_id)
        )

    @rx.event
    async def vaciar(self):
        """Empty the cart."""
        return await self._aplicar(carrito_servicio.vaciar)

    @rx.event
    async def reintentar(self):
        return await self.on_load()

    async def _cambiar(self, linea_id: int, cantidad: int):
        return await self._aplicar(
            lambda usuario: carrito_servicio.cambiar_cantidad(
                usuario, linea_id, cantidad
            )
        )

    async def _aplicar(self, operacion: Operacion):
        """Run a cart operation for the buyer; guests are sent to the login."""
        usuario_id = await self._usuario()
        if usuario_id is None:
            return rx.redirect(RUTA_LOGIN + RUTA_CARRITO)
        return self._ejecutar(operacion, usuario_id)

    def _ejecutar(self, operacion: Operacion, usuario_id: int):
        """Call the service, turning a known failure into a message (not a crash)."""
        try:
            carrito = operacion(usuario_id)
        except ErrorDeCarrito as error:
            self.error = str(error)
            return Toast(str(error), tone="error")
        except SQLAlchemyError:
            logger.exception("Fallo una operacion del carrito")
            self.error = MENSAJE_ERROR
            return Toast(MENSAJE_ERROR, tone="error")

        self.error = ""
        self._guardar(carrito)
        return None

    async def _usuario(self) -> int | None:
        """Resolve the buyer id from the session token (never from a client var)."""
        auth = await self.get_state(LocalAuthState)
        return usuario_autenticado(auth.auth_token)

    def _cargar(self, usuario_id: int) -> None:
        try:
            carrito = carrito_servicio.ver_carrito(usuario_id)
        except SQLAlchemyError:
            logger.exception("Fallo la carga del carrito")
            self.error = MENSAJE_ERROR
            self.cargando = False
            return
        self._guardar(carrito)

    def _guardar(self, carrito: CarritoDeCompra) -> None:
        self.lineas = [asdict(linea) for linea in carrito.lineas]
        self.total_unidades = carrito.total_unidades
        self.subtotal = carrito.subtotal
        self.cargando = False

    def _limpiar_vars(self) -> None:
        self.lineas = []
        self.total_unidades = 0
        self.subtotal = ""
        self.cargando = False

    def _cantidad(self, linea_id: int) -> int | None:
        for linea in self.lineas:
            if int(linea["id"]) == int(linea_id):
                return int(linea["cantidad"])
        return None

    def _ruta_actual(self) -> str:
        """Browser path, so the login sends the buyer back here (D-002)."""
        url = self.router.url
        ruta = url.get("path", "") if isinstance(url, dict) else getattr(url, "path", "")
        texto = str(ruta or "")
        if not texto.startswith("/") or texto.startswith("//"):
            return "/"
        return texto
