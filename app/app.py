"""Punto de entrada de la app.

Importar un modulo de pagina registra su ruta (usa ``@rx.page``). Login y
registro son paginas propias: el plugin solo aporta ``LocalUser``,
``LocalAuthSession`` y ``LocalAuthState``. Las dos pantallas del plugin estan en
ingles, y ademas el alta suya solo crea la credencial (T-022) y sus errores no
se pueden traducir sin reescribir el estado.

Estado actual: el catalogo en la raiz, el detalle, el carrito, el checkout y las
dos pantallas de sesion. El panel del admin se reconstruye en las fases
siguientes, despues de que la Fase 5 borrara el codigo viejo que dependia de los
modelos eliminados (T-060).
"""

import reflex as rx

from app.pages.catalogo_pagina import catalogo_pagina  # noqa: F401  (registra "/")
from app.pages.carrito_pagina import carrito_pagina  # noqa: F401  (registra "/carrito")
from app.pages.checkout_pagina import checkout_pagina  # noqa: F401  (registra "/checkout")
from app.pages.login_pagina import login_pagina  # noqa: F401  (registra "/login")
from app.pages.producto_pagina import (  # noqa: F401  (registra "/producto/[producto_id]")
    producto_pagina,
)
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
