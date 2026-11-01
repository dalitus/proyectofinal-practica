"""Datos de la sesión para el header y el logout (T-021, D-018).

El header necesita saber quién está conectado en cualquier página, sin que cada
página cargue un estado extra. Por eso ``cuenta`` es una var calculada con caché:
Reflex la recalcula cuando cambia ``auth_token`` (login o logout) y, si nada
cambia, cada 10 minutos como el resto del plugin.

``cerrar_sesion`` borra la fila de ``localauthsession`` del token, vacía el token
del navegador y limpia el carrito visible: el carrito del comprador sigue en la
base para cuando vuelva, pero la pantalla no puede mostrar líneas ajenas.

El estado no abre sesiones ni importa el engine (T-062): pregunta al servicio.
"""

from __future__ import annotations

from typing import Any

import reflex as rx
from reflex_local_auth.local_auth import DEFAULT_AUTH_REFRESH_DELTA, LocalAuthState

from app.service import auth_servicio
from app.service.sesion_servicio import ADMIN, rol, usuario_autenticado
from app.state.carrito_estado import CarritoEstado

SIN_SESION: dict[str, Any] = {"logueado": False, "nombre": "", "es_admin": False}


class SesionEstado(LocalAuthState):
    """Quién está conectado, para el header de todas las páginas."""

    @rx.var(cache=True, interval=DEFAULT_AUTH_REFRESH_DELTA, initial_value=SIN_SESION)
    def cuenta(self) -> dict[str, Any]:
        """Name, role and session flag; a dead token counts as a guest."""
        usuario_id = usuario_autenticado(self.auth_token)
        if usuario_id is None:
            return dict(SIN_SESION)

        perfil = auth_servicio.obtener_perfil(usuario_id)
        nombre = f"{perfil.nombre} {perfil.apellido}".strip() if perfil else ""
        return {
            "logueado": True,
            "nombre": nombre,
            "es_admin": rol(self.auth_token) == ADMIN,
        }

    @rx.event
    async def cerrar_sesion(self):
        """Delete the server session, forget the token and go to the catalog."""
        # El plugin borra las filas de la base pero no limpia el token: si queda
        # en el navegador, el próximo pedido viaja con una sesión muerta.
        self.do_logout()
        self.auth_token = ""

        carrito = await self.get_state(CarritoEstado)
        carrito.limpiar_visible()

        return rx.redirect("/")
