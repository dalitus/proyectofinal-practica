"""Estado del checkout (T-043, D-005, D-032).

El checkout es una pagina, no un asistente (D-032): se revisan los datos, se
confirma y se muestra el numero de pedido. No hay pago online: el pedido queda
registrado y el envio se coordina despues (D-005).

El total no viaja en el formulario: el servicio lo recalcula desde el carrito, asi
que editar la pagina no cambia lo que paga el comprador (D-003, T-032).

El id del comprador se resuelve desde el token de ``LocalAuthState`` con
``sesion_servicio``, nunca desde una var del cliente. El estado no abre sesiones
ni importa el engine (T-062) y el detalle tecnico va al log (T-064).
"""

from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Any

import reflex as rx
from reflex_local_auth.local_auth import LocalAuthState
from sqlalchemy.exc import SQLAlchemyError

from app.service import carrito_servicio, pedido_servicio
from app.service.carrito_servicio import CarritoDeCompra
from app.service.pedido_servicio import (
    ErrorDePedido,
    errores_de_entrega,
    validar_entrega,
)
from app.service.sesion_servicio import usuario_autenticado
from app.ui import Toast

logger = logging.getLogger(__name__)

MENSAJE_CARGA = "No pudimos cargar el checkout. Proba de nuevo en unos segundos."
MENSAJE_CONFIRMAR = "No pudimos confirmar el pedido. Proba de nuevo en unos segundos."

RUTA_CARRITO = "/carrito"
RUTA_LOGIN = "/login?next=/checkout"
RUTA_CATALOGO = "/"

# Los cuatro obligatorios de `pedido_servicio`: campo -> var de error.
CAMPOS_CON_ERROR = ("direccion", "numero", "ciudad", "provincia")


class CheckoutEstado(rx.State):
    """Formulario de entrega, resumen del carrito y confirmacion del pedido."""

    # Resumen ya formateado por el servicio.
    lineas: list[dict[str, Any]] = []
    subtotal: str = ""
    total_unidades: int = 0

    cargando: bool = True
    enviando: bool = False
    error: str = ""
    error_confirmacion: str = ""

    # Pedido confirmado: 0 mientras no se haya comprado.
    pedido_id: int = 0
    total_confirmado: str = ""
    entrega_confirmada: str = ""

    # Formulario controlado para que un error no borre lo escrito.
    direccion: str = ""
    numero: str = ""
    departamento: str = ""
    codigo_postal: str = ""
    ciudad: str = ""
    provincia: str = ""

    # Error por campo, junto al input (design.md 5).
    error_direccion: str = ""
    error_numero: str = ""
    error_ciudad: str = ""
    error_provincia: str = ""

    @rx.var
    def confirmado(self) -> bool:
        return self.pedido_id > 0

    @rx.var
    def resumen(self) -> str:
        """Short line for the page header."""
        if self.confirmado:
            return "Compra registrada."
        total = self.total_unidades
        if total == 1:
            return "1 producto para confirmar."
        return f"{total} productos para confirmar."

    @rx.event
    async def on_load(self):
        """Load the cart or send the buyer to the login / the cart (D-002)."""
        if self.confirmado:
            return None

        self.cargando = True
        self.error = ""
        self.error_confirmacion = ""

        usuario_id = await self._usuario()
        if usuario_id is None:
            return rx.redirect(RUTA_LOGIN)

        self._cargar(usuario_id)
        if not self.lineas:
            return rx.redirect(RUTA_CARRITO)
        return None

    @rx.event
    async def reintentar(self):
        return await self.on_load()

    # Setters explicitos: el formulario es controlado para no perder lo escrito
    # cuando aparece un error por campo.
    @rx.event
    def set_direccion(self, value: str) -> None:
        self.direccion = value

    @rx.event
    def set_numero(self, value: str) -> None:
        self.numero = value

    @rx.event
    def set_departamento(self, value: str) -> None:
        self.departamento = value

    @rx.event
    def set_codigo_postal(self, value: str) -> None:
        self.codigo_postal = value

    @rx.event
    def set_ciudad(self, value: str) -> None:
        self.ciudad = value

    @rx.event
    def set_provincia(self, value: str) -> None:
        self.provincia = value

    @rx.event
    async def confirmar(self, form_data: dict[str, Any]):
        """Validate the delivery data, create the order and show its number."""
        self.error = ""
        self.error_confirmacion = ""
        self._limpiar_errores()

        usuario_id = await self._usuario()
        if usuario_id is None:
            return rx.redirect(RUTA_LOGIN)

        faltantes = errores_de_entrega(form_data)
        if faltantes:
            self._aplicar_errores(faltantes)
            return None

        try:
            entrega = validar_entrega(form_data)
        except ErrorDePedido as error:
            self.error = str(error)
            return None

        # Lo escrito se conserva en el estado aunque el formulario se re-renderice.
        self.direccion = entrega.direccion
        self.numero = entrega.numero
        self.departamento = entrega.departamento
        self.codigo_postal = entrega.codigo_postal
        self.ciudad = entrega.ciudad
        self.provincia = entrega.provincia

        self.enviando = True
        try:
            pedido_id = pedido_servicio.confirmar_pedido(usuario_id, entrega)
        except ErrorDePedido as error:
            # El carrito pudo cambiar entre la carga y la confirmacion (D-004):
            # se muestra el motivo y el resumen real, sin inventar el total.
            self.error_confirmacion = str(error)
            self._cargar(usuario_id)
            if not self.lineas:
                return rx.redirect(RUTA_CARRITO)
            return Toast(str(error), tone="error")
        except SQLAlchemyError:
            logger.exception("Fallo la confirmacion del pedido")
            self.error_confirmacion = MENSAJE_CONFIRMAR
            return Toast(MENSAJE_CONFIRMAR, tone="error")
        finally:
            self.enviando = False

        self.total_confirmado = self.subtotal
        self.entrega_confirmada = self._formatear_entrega(entrega)
        self.pedido_id = pedido_id
        self.lineas = []
        self.total_unidades = 0
        self.subtotal = ""
        return Toast("Pedido confirmado")

    async def _usuario(self) -> int | None:
        auth = await self.get_state(LocalAuthState)
        return usuario_autenticado(auth.auth_token)

    def _cargar(self, usuario_id: int) -> None:
        try:
            carrito = carrito_servicio.ver_carrito(usuario_id)
        except SQLAlchemyError:
            logger.exception("Fallo la carga del checkout")
            self.error = MENSAJE_CARGA
            self.cargando = False
            return
        self._guardar(carrito)

    def _guardar(self, carrito: CarritoDeCompra) -> None:
        self.lineas = [asdict(linea) for linea in carrito.lineas]
        self.total_unidades = carrito.total_unidades
        self.subtotal = carrito.subtotal
        self.cargando = False

    def _limpiar_errores(self) -> None:
        self.error_direccion = ""
        self.error_numero = ""
        self.error_ciudad = ""
        self.error_provincia = ""

    def _aplicar_errores(self, errores: dict[str, str]) -> None:
        for campo in CAMPOS_CON_ERROR:
            setattr(self, f"error_{campo}", errores.get(campo, ""))

    @staticmethod
    def _formatear_entrega(entrega: Any) -> str:
        """One readable line for the confirmation view."""
        calle = f"{entrega.direccion} {entrega.numero}".strip()
        piso = f", {entrega.departamento}" if entrega.departamento else ""
        cp = f" (CP {entrega.codigo_postal})" if entrega.codigo_postal else ""
        return f"{calle}{piso}, {entrega.ciudad}, {entrega.provincia}{cp}"
