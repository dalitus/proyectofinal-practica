"""Guarda de las rutas del admin (T-023, D-021).

Las pantallas de admin heredan de ``AdminEstado``: ``_iniciar`` resuelve el rol
contra la base y redirige antes de que la pagina pinte un solo dato. Ocultar un
boton no es un permiso; esto corre en el servidor.

La subclase implementa ``_cargar`` y declara sus propios eventos ``on_load`` y
``reintentar``. No es repeticion gratuita: en Reflex un handler heredado queda
atado a la clase que lo define (``EventHandler.state``), asi que el evento
correria sobre una instancia de ``AdminEstado`` y llamaria al ``_cargar`` de la
base. Declararlos en la subclase los ata a la instancia correcta.

Cada accion que escribe vuelve a llamar a ``_exigir_admin``: una sesion que
vencio mientras la pagina estaba abierta no puede cambiar un pedido.
"""

from __future__ import annotations

import reflex as rx
from reflex_local_auth.local_auth import LocalAuthState

from app.service.sesion_servicio import (
    ADMIN,
    INVITADO,
    rol,
    usuario_autenticado,
)
from app.state.parametros import ruta_interna

RUTA_LOGIN = "/login?next="
RUTA_SIN_PERMISO = "/403"


class AdminEstado(rx.State):
    """Base de las pantallas de admin: rol resuelto y estado de carga."""

    autorizado: bool = False
    cargando: bool = True
    error: str = ""
    admin_id: int = 0

    async def _iniciar(self):
        """Resolve the role and load the page, or return the redirect."""
        self.cargando = True
        self.error = ""
        self.autorizado = False

        destino = await self._exigir_admin()
        if destino is not None:
            return destino

        self._cargar()
        return None

    async def _exigir_admin(self):
        """Return a redirect when the role is not admin, or ``None``."""
        destino = await self._destino_si_no_puede()
        if destino is not None:
            return destino

        auth = await self.get_state(LocalAuthState)
        self.admin_id = usuario_autenticado(auth.auth_token) or 0
        self.autorizado = True
        return None

    async def _destino_si_no_puede(self):
        """Guest goes to the login, a buyer to the 403 page (D-021)."""
        auth = await self.get_state(LocalAuthState)
        actual = rol(auth.auth_token)

        if actual == INVITADO:
            return rx.redirect(RUTA_LOGIN + self._ruta_actual())
        if actual != ADMIN:
            return rx.redirect(RUTA_SIN_PERMISO)
        return None

    def _cargar(self) -> None:
        """Load the data of the page; every admin state overrides this."""
        raise NotImplementedError

    def _ruta_actual(self) -> str:
        """Browser path, so the login sends the admin back here."""
        return ruta_interna(self.router.url, "/admin/pedidos")
