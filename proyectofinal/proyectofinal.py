import reflex as rx

# Importar cada modulo de pagina es lo que registra su ruta, porque cada uno
# usa el decorador @rx.page(route=..., title=..., on_load=...).
from proyectofinal.pages.users_page import users_page
from proyectofinal.pages.catalogo_page import catalogo_page
from proyectofinal.pages.andmin_page import admin_login_page
from proyectofinal.pages.adnmin_shouder_page import admin_dashboard_page
from proyectofinal.pages.ubicaccion_page import ubicaccion_page
from proyectofinal.pages.carrito_page import carrito_page
from proyectofinal.pages.producto_detalle_page import detalle_producto_page

from proyectofinal.pages.consulta_usuario_page import consulta_usuario_page
from proyectofinal.pages.consulta_admin_page import consulta_admin_page
#from proyectofinal.pages.compras_admin_page import compras_admin_page
from proyectofinal.pages.pedidos_page import pedidos_page
from proyectofinal.pages.pedidos_admin_page import pedidos_admin_page

from proyectofinal.state.catalogo_state import CatalogoState


class UsersState(rx.State):
    pass


# La UI es solo clara: las páginas pintan fondos blancos, así que hay que
# neutralizar el modo oscuro que el navegador guardó en localStorage (el valor
# por defecto de versiones anteriores era "system"). Se ejecuta antes de que
# React monte el ThemeProvider.
FORCE_LIGHT_THEME = rx.el.script(
    "try{localStorage.setItem('theme','light');"
    "localStorage.setItem('last_compiled_theme','light');}catch(e){}",
    type="text/javascript",
)

app = rx.App(head_components=[FORCE_LIGHT_THEME])

# La ruta raiz reutiliza el catalogo. Se registra aca (y no con un decorador)
# para que "/" y "/catalogo" compartan el mismo componente, con el on_load
# necesario para que el catalogo tenga productos desde la primera carga.
app.add_page(
    catalogo_page,
    route="/",
    title="Catálogo",
    on_load=CatalogoState.cargar_productos,
)
