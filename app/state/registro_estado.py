"""Estado del formulario de alta de comprador.

El estado no abre sesiones ni importa el engine (T-062): delega en
``app.service.auth_servicio``, que abre y cierra su propia sesion (D-033).

La pagina de registro del plugin ``reflex-local-auth`` no se usa porque crea
``LocalUser`` por su cuenta y deja el alta sin ``UserProfile``; el perfil es la
tabla de la que cuelgan pedidos, consultas y el rol de cada cuenta.
"""

import reflex as rx

from app.service.auth_servicio import ErrorDeRegistro, registrar_comprador


class RegistroState(rx.State):
    """Formulario de alta de una cuenta de comprador."""

    nombre: str = ""
    email: str = ""
    password: str = ""
    confirmacion: str = ""
    error: str = ""
    enviando: bool = False

    def _limpiar_passwords(self) -> None:
        """Drop both password fields so they never stay in the browser state."""
        self.password = ""
        self.confirmacion = ""

    @rx.event
    def set_nombre(self, value: str) -> None:
        self.nombre = value

    @rx.event
    def set_email(self, value: str) -> None:
        self.email = value

    @rx.event
    def set_password(self, value: str) -> None:
        self.password = value

    @rx.event
    def set_confirmacion(self, value: str) -> None:
        self.confirmacion = value

    @rx.event
    def enviar(self):
        """Create the buyer account and send the user to the login page."""
        self.error = ""

        if self.password != self.confirmacion:
            self.error = "Las contraseñas no coinciden."
            self._limpiar_passwords()
            return

        self.enviando = True
        try:
            registrar_comprador(
                email=self.email,
                password=self.password,
                nombre=self.nombre,
            )
        except ErrorDeRegistro as error:
            self.error = str(error)
            self._limpiar_passwords()
            return
        finally:
            self.enviando = False

        self.nombre = ""
        self.email = ""
        self._limpiar_passwords()
        return rx.redirect("/login")
