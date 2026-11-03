"""Guarda de las rutas del comprador (T-065, T-076, D-002).

Las pantallas del comprador heredan de ``CompradorEstado``: la sesion se resuelve
contra la base antes de pintar un dato y el invitado vuelve al login con la ruta
de vuelta. No hay rol minimo: cualquier usuario con sesion viva entra, y el
``usuario_id`` sale del token, nunca de una var del cliente.

Igual que ``AdminEstado``, la subclase declara sus propios ``on_load`` y
``reintentar``: en Reflex un handler heredado queda atado a la clase que lo
define y correria sobre la instancia base.
"""

from __future__ import annotations

import reflex as rx
from reflex_local_auth.local_auth import LocalAuthState

from app.service.sesion_servicio import usuario_con_rol
from app.state.parametros import ruta_interna

RUTA_LOGIN = "/login?next="


class CompradorEstado(rx.State):
    """Base de las pantallas del comprador: sesion resuelta y estado de carga."""

    autorizado: bool = False
    cargando: bool = True
    error: str = ""
    usuario_id: int = 0

    async def _iniciar(self):
        """Resolve the session and load the page, or return the redirect."""
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
            return rx.redirect(RUTA_LOGIN + self._ruta_actual())

        self.usuario_id = usuario_id
        self.autorizado = True
        return None

    def _cargar(self) -> None:
        """Load the data of the page; every buyer state overrides this."""
        raise NotImplementedError

    def _ruta_actual(self) -> str:
        """Browser path, so the login sends the buyer back here."""
        return ruta_interna(self.router.url, "/")
