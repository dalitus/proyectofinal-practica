"""Estado del formulario de inicio de sesión (T-021, D-018).

El estado no abre sesiones ni importa el engine (T-062): valida las credenciales
con ``app.service.auth_servicio.autenticar``, que abre y cierra su propia sesión
(D-033). La sesión de Reflex la sigue manejando ``LocalAuthState`` con
``_login``: el estado solo le pasa el id del usuario ya verificado.

``destino`` conserva la página que el invitado quería ver (``?next=``) para
volver ahí después de entrar. Solo se aceptan rutas internas: un valor absoluto
o con ``//`` sería un redirect abierto.
"""

from __future__ import annotations

import logging
from typing import Any

import reflex as rx
from reflex_local_auth.local_auth import LocalAuthState

from app.service.auth_servicio import ErrorDeAcceso, autenticar

logger = logging.getLogger(__name__)

DESTINO_POR_DEFECTO = "/"
MENSAJE_ERROR = "No pudimos iniciar sesión. Probá de nuevo en unos segundos."


class LoginEstado(LocalAuthState):
    """Formulario único de login: email + contraseña (D-018)."""

    email: str = ""
    password: str = ""
    error: str = ""
    enviando: bool = False
    destino: str = DESTINO_POR_DEFECTO

    @rx.event
    def on_load(self) -> None:
        """Read ``?next=`` so login can return to the page the guest wanted."""
        pedido = self.router.page.params.get("next", "")
        es_interna = pedido.startswith("/") and not pedido.startswith("//")
        self.destino = pedido if es_interna else DESTINO_POR_DEFECTO
        self.error = ""

    @rx.event
    def set_email(self, value: str) -> None:
        self.email = value

    @rx.event
    def set_password(self, value: str) -> None:
        self.password = value

    @rx.event
    def enviar(self, form_data: dict[str, Any]):
        """Authenticate and go back to the origin page (T-021)."""
        self.error = ""
        self.enviando = True
        try:
            user_id = autenticar(
                email=form_data.get("email", ""),
                password=form_data.get("password", ""),
            )
        except ErrorDeAcceso as error:
            self.error = str(error)
            return
        except Exception:  # la DB puede estar caída: el detalle va al log (T-064)
            logger.exception("Falló el login de %s", self.email)
            self.error = MENSAJE_ERROR
            return
        finally:
            self.enviando = False
            self.password = ""

        self._login(user_id)
        self.email = ""
        return rx.redirect(self.destino)
