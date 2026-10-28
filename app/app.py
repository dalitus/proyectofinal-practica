"""Punto de entrada de la app.

Importar un modulo de pagina registra su ruta (usa ``@rx.page``). La pantalla
de login viene del plugin y se monta con ``add_page``; la de registro es propia
y se registra sola, porque el alta tiene que crear ``LocalUser`` + ``UserProfile``
y la del plugin solo crea la credencial (T-022).

Estado actual: solo la raiz y las dos pantallas de sesion. El catalogo, el
carrito y el panel del admin se reconstruyen en las fases siguientes, despues
de que la Fase 5 borrara el codigo viejo que dependia de los modelos
eliminados (T-060).
"""

import reflex as rx
import reflex_local_auth

from app.pages.inicio_pagina import inicio_pagina  # noqa: F401  (registra "/")
from app.pages.registro_pagina import registro_pagina  # noqa: F401  (registra "/register")
from app.ui import APP_CSS, FONT_HEAD_COMPONENTS

# La UI es solo clara: las paginas pintan fondos blancos, asi que hay que
# neutralizar el modo oscuro que el navegador guardo en localStorage (el valor
# por defecto de versiones anteriores era "system"). Se ejecuta antes de que
# React monte el ThemeProvider.
FORCE_LIGHT_THEME = rx.el.script(
    "try{localStorage.setItem('theme','light');"
    "localStorage.setItem('last_compiled_theme','light');}catch(e){}",
    type="text/javascript",
)

# El sistema de diseno vive en un unico stylesheet: app/ui/styles.py traduce los
# tokens a variables CSS y ahi viven :hover, :focus-visible y las media queries,
# cosas que el prop inline `style` no puede expresar (T-063).
app = rx.App(
    head_components=[
        FORCE_LIGHT_THEME,
        *FONT_HEAD_COMPONENTS,
        rx.el.style(APP_CSS),
    ]
)

app.add_page(
    reflex_local_auth.pages.login_page,
    route=reflex_local_auth.routes.LOGIN_ROUTE,
    title="Iniciar sesion",
)
