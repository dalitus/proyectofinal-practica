import reflex as rx
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

class UsersState(rx.State):
    pass

app = rx.App()
 
app.add_page(users_page, route="/user", title="Usuarios")
app.add_page(catalogo_page, route="/", title="Catálogo")
app.add_page(admin_login_page, route="/admin_login", title="Login Admin")
app.add_page(admin_dashboard_page, route="/admin_dashboard", title="Panel Admin")
app.add_page(ubicaccion_page, route="/ubicacion", title="Ubicación")
app.add_page(carrito_page, route="/carrito", title="Carrito de Compra")
app.add_page(detalle_producto_page, route="/detalle_producto", title="Detalle Producto")

app.add_page(consulta_usuario_page, route="/consulta_usuario", title="Consulta Usuario")  
app.add_page(consulta_admin_page, route="/consulta_admin", title="Consulta Admin")
#app.add_page(compras_admin_page, route="/compras_admin", title="Compras Admin")
app.add_page(pedidos_page, route="/pedidos", title="Mis Pedidos")
app.add_page(pedidos_admin_page, route="/pedidos_admin", title="Gestión de Pedidos")
