"""Punto de entrada de la app.

Importar un modulo de pagina registra su ruta (usa ``@rx.page``). Login y
registro son paginas propias: el plugin solo aporta ``LocalUser``,
``LocalAuthSession`` y ``LocalAuthState``. Las dos pantallas del plugin estan en
ingles, y ademas el alta suya solo crea la credencial (T-022) y sus errores no
se pueden traducir sin reescribir el estado.

Estado actual: el catalogo en la raiz, el detalle, el carrito, el checkout, las
dos pantallas de sesion, los pedidos y consultas del comprador y el panel del
admin (productos, pedidos y consultas).
"""

import reflex as rx

from app.pages.catalogo_pagina import catalogo_pagina  # noqa: F401  (registra "/")
from app.pages.carrito_pagina import carrito_pagina  # noqa: F401  (registra "/carrito")
from app.pages.checkout_pagina import checkout_pagina  # noqa: F401  (registra "/checkout")
from app.pages.consulta_admin_pagina import (  # noqa: F401  (registra "/admin/consultas/[consulta_id]")
    consulta_admin_pagina,
)
from app.pages.consultas_admin_pagina import (  # noqa: F401  (registra "/admin/consultas")
    consultas_admin_pagina,
)
from app.pages.login_pagina import login_pagina  # noqa: F401  (registra "/login")
from app.pages.mi_pedido_pagina import (  # noqa: F401  (registra "/pedidos/[pedido_id]")
    mi_pedido_pagina,
)
from app.pages.mis_consultas_pagina import (  # noqa: F401  (registra "/consultas")
    mis_consultas_pagina,
)
from app.pages.mis_pedidos_pagina import (  # noqa: F401  (registra "/pedidos")
    mis_pedidos_pagina,
)
from app.pages.no_autorizado_pagina import (  # noqa: F401  (registra "/403")
    no_autorizado_pagina,
)
from app.pages.no_encontrada_pagina import (  # noqa: F401  (registra "/404")
    no_encontrada_pagina,
)
from app.pages.pedido_admin_pagina import (  # noqa: F401  (registra "/admin/pedidos/[pedido_id]")
    pedido_admin_pagina,
)
from app.pages.pedidos_admin_pagina import (  # noqa: F401  (registra "/admin/pedidos")
    pedidos_admin_pagina,
)
from app.pages.producto_admin_pagina import (  # noqa: F401  (registra "/admin/productos/[producto_id]")
    producto_admin_pagina,
)
from app.pages.producto_nuevo_pagina import (  # noqa: F401  (registra "/admin/productos/nuevo")
    producto_nuevo_pagina,
)
from app.pages.productos_admin_pagina import (  # noqa: F401  (registra "/admin/productos")
    productos_admin_pagina,
)
from app.pages.producto_pagina import (  # noqa: F401  (registra "/producto/[producto_id]")
    producto_pagina,
)
from app.pages.redirecciones_pagina import (  # noqa: F401  (rutas viejas -> URL canonica)
    redireccion_catalogo,
    redireccion_detalle,
    redireccion_user,
    redireccion_users,
)
from app.pages.registro_pagina import registro_pagina  # noqa: F401  (registra "/register")
from app.service.auditoria import configurar_destino
from app.ui import APP_CSS, FONT_HEAD_COMPONENTS

# Sin esto, las líneas de auditoría (D-031) se escriben en un logger sin destino
# y se pierden: Reflex no configura el logging de la aplicación.
configurar_destino()

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
