import reflex as rx
import re
from proyectofinal.model.product_model import Producto
from proyectofinal.service.producto_servicio import (
    obtener_productos,
    crear_producto,
    eliminar_producto,
    editar_producto
)
from proyectofinal.pages.ui_helpers import PrimaryButton, SecondaryButton, DangerButton, PageHeader
from proyectofinal.repository.catalogo_repository import get_all_productos
from proyectofinal.service.servicio_stock import obtener_stocks_por_producto
from proyectofinal.service.servicio_stock import editar_stock, crear_stock, obtener_stocks_por_producto

class AdminState(rx.State):
    productos: list[dict] = []
    error_message: str = ""
    producto_id_a_eliminar: int = 0
    producto_id_a_editar: int = 0
    datos_edicion: dict = {}
    imagen_local: str = ""
    preview_data_url: str = ""
    modal_crear_abierto: bool = False
    modal_editar_abierto: bool = False

    colores: list[dict] = []
    cantidad_total: int = 0

    def agregar_color(self):
        # Agregar un nuevo color vacío con cantidad 0
        self.colores = self.colores + [{"color": "", "cantidad": 0}]
        # Recalcular el total
        self.actualizar_total()
        # 👇 Mantener el modal abierto
        self.modal_editar_abierto = True

    def actualizar_color(self, index: int, nuevo_color: str):
        self.colores[index]["color"] = nuevo_color
        self.colores = self.colores[:]

    def actualizar_cantidad(self, index: int, nueva_cantidad: str):
        try:
            self.colores[index]["cantidad"] = int(nueva_cantidad)
        except ValueError:
            self.colores[index]["cantidad"] = 0
        self.colores = self.colores[:]
        self.actualizar_total()

    def actualizar_total(self):
        self.cantidad_total = sum(c.get("cantidad", 0) for c in self.colores)

    @rx.event
    def cargar_productos(self):
        productos = []
        for p in get_all_productos():
            d = p.dict()
            d["cantidad_total"] = p.cantidad_total
            d["stocks"] = [s.dict() for s in p.stocks]
            # 👇 preparar campos ya formateados como texto
            d["precio_text"] = f"${p.precio}"
            d["cantidad_total_text"] = str(p.cantidad_total)
            d["stocks_text"] = "\n".join(
                [f"{s['color']}: {s['cantidad_disponible']}" for s in d["stocks"]]
            )
            productos.append(d)
        self.productos = productos

    @rx.event
    def abrir_modal_crear(self):
        self.modal_crear_abierto = True
        self.error_message = ""
        self.imagen_local = ""
        self.preview_data_url = ""

    @rx.event
    def cerrar_modal_crear(self):
        self.modal_crear_abierto = False
        self.error_message = ""
        self.imagen_local = ""
        self.preview_data_url = ""

    @rx.event
    def abrir_modal_editar(self, producto_id: int, data: dict):
        self.modal_editar_abierto = True
        self.producto_id_a_editar = producto_id
        self.datos_edicion = data
        self.error_message = ""
        self.imagen_local = ""
        self.preview_data_url = ""

        # 👇 Cargar los stocks actuales del producto
        try:
            stocks = obtener_stocks_por_producto(producto_id)
            self.colores = [
                {
                    "id_stock": s.id_stock,
                    "color": s.color,
                    "cantidad": s.cantidad_disponible
                }
                for s in stocks
            ]
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.colores = []

    @rx.event
    def cerrar_modal_editar(self):
        self.modal_editar_abierto = False
        self.producto_id_a_editar = 0
        self.datos_edicion = {}
        self.error_message = ""
        self.imagen_local = ""
        self.preview_data_url = ""

    @rx.event
    def set_modal_crear_abierto(self, abierto: bool):
        self.modal_crear_abierto = abierto

    @rx.event
    def set_modal_editar_abierto(self, abierto: bool):
        self.modal_editar_abierto = abierto

    @rx.event
    def crear_producto(self, data: dict):
        try:
            print("Datos recibidos:", data)
            imagen_entrada = data.get("imagen")
            if (not imagen_entrada or imagen_entrada.strip() == "") and self.imagen_local:
                imagen_entrada = self.imagen_local

            # Validaciones mínimas
            if not data.get("nombre") or not data.get("precio"):
                self.error_message = "Nombre y precio son obligatorios"
                return

            # Validar formato de campos con regex
            import re
            pat = re.compile(r'^[A-Za-z0-9ÁÉÍÓÚáéíóúÑñÜü\s\-_,\.]{1,100}$')
            for campo in ("nombre", "marca", "categoria", "talle"):
                val = (data.get(campo) or "").strip()
                if val == "":
                    continue
                if not pat.match(val):
                    self.error_message = f"{campo.capitalize()} contiene caracteres inválidos"
                    return

            try:
                precio_val = float(data["precio"])
            except Exception:
                self.error_message = "Precio inválido"
                return

            # Crear producto en la tabla productos
            nuevo = crear_producto(
                nombre=data["nombre"],
                descripcion=data.get("descripcion", ""),
                precio=precio_val,
                marca=data.get("marca", ""),
                categoria=data.get("categoria", ""),
                talle=data.get("talle", ""),
                imagen=imagen_entrada,
            )

            # Guardar colores en Stocks
            from proyectofinal.service.servicio_stock import crear_stock
            for c in self.colores:
                if c["color"].strip() != "":
                    crear_stock(
                        id_producto=nuevo.id_producto,
                        color=c["color"],
                        cantidad_disponible=int(c["cantidad"])
                    )

            # Refrescar lista de productos
            self.cargar_productos()
            self.error_message = ""
            self.imagen_local = ""
            self.preview_data_url = ""
            self.colores = []  # limpiar lista
            self.modal_crear_abierto = False
            return rx.toast("Producto creado correctamente")

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error_message = f"Error al crear producto: {e}"

    @rx.event
    def set_producto_a_eliminar(self, producto_id: int):
        self.producto_id_a_eliminar = producto_id

    @rx.event
    def confirmar_eliminacion(self):
        self.eliminar_producto(self.producto_id_a_eliminar)

    @rx.event
    def eliminar_producto(self, producto_id: int):
        try:
            # eliminar stocks asociados primero
            from proyectofinal.service.servicio_stock import obtener_stocks_por_producto, eliminar_stock
            stocks = obtener_stocks_por_producto(producto_id)
            for s in stocks:
                eliminar_stock(s.id_stock)

            # luego eliminar el producto
            if eliminar_producto(producto_id):
                self.cargar_productos()
                self.error_message = ""
            else:
                self.error_message = "Error al eliminar producto: Producto no encontrado"
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error_message = f"Error al eliminar producto: {e}"
        finally:
            self.producto_id_a_eliminar = 0

    @rx.event
    def set_edicion(self, producto_id: int, data: dict):
        self.producto_id_a_editar = producto_id
        self.datos_edicion = data

    @rx.event
    def confirmar_edicion(self):
        self.editar_producto(self.producto_id_a_editar, self.datos_edicion)

    @rx.event
    def editar_producto(self, producto_id: int, data: dict):
        try:
            # Normalizar y filtrar valores vacíos
            cleaned: dict = {}
            for k, v in (data or {}).items():
                if v is None:
                    continue
                try:
                    s = v.strip()
                except Exception:
                    s = str(v).strip()
                if s != "":
                    cleaned[k] = v
            data = cleaned

            # 👇 Manejo de imagen: si hay imagen_local, usarla
            if self.imagen_local:
                data["imagen_url"] = self.imagen_local
            elif "imagen" in data:
                # renombrar campo para que coincida con lo que muestra la tabla
                data["imagen_url"] = data.pop("imagen")

            # Actualizar campos del producto
            from proyectofinal.service.producto_servicio import editar_producto
            actualizado = editar_producto(producto_id, data)
            if not actualizado:
                self.error_message = "Producto no encontrado"
                return

            # Actualizar o crear stocks asociados
            from proyectofinal.service.servicio_stock import editar_stock, crear_stock, obtener_stocks_por_producto
            for c in self.colores:
                if "id_stock" in c:
                    editar_stock(c["id_stock"], {
                        "color": c["color"],
                        "cantidad_disponible": int(c["cantidad"])
                    })
                else:
                    crear_stock(producto_id, c["color"], int(c["cantidad"]))

            # Recalcular el total de stock
            total = sum(s.cantidad_disponible for s in obtener_stocks_por_producto(producto_id))
            self.datos_edicion["cantidad_total"] = total

            # Refrescar lista de productos
            self.cargar_productos()
            self.error_message = ""
            self.modal_editar_abierto = False
            return rx.toast("Producto actualizado correctamente")

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error_message = f"Error al editar producto: {e}"
        finally:
            self.imagen_local = ""
            self.preview_data_url = ""

    @rx.event
    def enviar_edicion(self, data: dict):
        # usar el producto seleccionado actualmente
        self.editar_producto(self.producto_id_a_editar, data)

@rx.page(route="admin_dashboard", title="Admin Dashboard", on_load=AdminState.cargar_productos)
def admin_dashboard_page() -> rx.Component:
    return rx.box(
        rx.flex(
            PageHeader("Panel de Administración de Productos", "Gestioná productos y consultas"),
            PrimaryButton("Ir a consultas de usuarios", on_click=ir_a_consultas, width="100%"),
            SecondaryButton("Gestionar Pedidos", on_click=ir_a_pedidos, width="100%"),
            crear_producto_dialog_component(),
            table_productos(),
            rx.cond(
                AdminState.error_message != "",
                rx.text(AdminState.error_message, color="red")
            ),
            eliminar_producto_dialog(),
            direction="column",
            style={"width": "70vw", "margin": "auto"}
        ),
        style={
            "background_color": "#ADD8E6",  # celeste
            "min_height": "100vh",          # ocupa toda la pantalla
            "padding": "20px"
        }
    )

def ir_a_consultas():
    return rx.redirect("/consulta_admin")


def ir_a_compras():
    return rx.redirect("/compras_admin")


def ir_a_pedidos():
    return rx.redirect("/pedidos_admin")

def render_fila_producto(p: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(p["id_producto"])),          # ID
        rx.table.cell(rx.text(p["nombre"])),               # Nombre
        rx.table.cell(
            rx.cond(
                p.get("imagen_url"),
                rx.image(src=p.get("imagen_url"), width="50px"),
                rx.image(src=p.get("imagen", ""), width="50px")
            )
        ),
        rx.table.cell(rx.text(p["precio_text"])),          # Precio
        rx.table.cell(rx.text(p["marca"])),                # Marca
        rx.table.cell(rx.text(p["talle"])),                # Talle
        rx.table.cell(rx.text(p["cantidad_total_text"])),  # Cantidad total
        rx.table.cell(rx.text(p["stocks_text"])),          # Stocks por color
        rx.table.cell(
            rx.hstack(
                rx.button(
                    "Eliminar",
                    color_scheme="red",
                    on_click=lambda _: AdminState.set_producto_a_eliminar(p["id_producto"])
                ),
                editar_producto_dialog_component(p)
            )
        )
    )

def table_productos() -> rx.Component:
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.cell(rx.text("ID")),
                rx.table.cell(rx.text("Nombre")),
                rx.table.cell(rx.text("Imagen")),
                rx.table.cell(rx.text("Precio")),
                rx.table.cell(rx.text("Marca")),
                rx.table.cell(rx.text("Talle")),
                rx.table.cell(rx.text("Cantidad")),
                rx.table.cell(rx.text("Stocks")),
                rx.table.cell(rx.text("Acciones")),
            )
        ),
        rx.table.body(
            rx.foreach(AdminState.productos, render_fila_producto)
        )
    )

def eliminar_producto_dialog() -> rx.Component:
    return rx.alert_dialog.root(
        rx.alert_dialog.trigger(rx.fragment()),  # invisible trigger
        rx.alert_dialog.content(
            rx.text("¿Eliminar producto? Esta acción no se puede deshacer."),
            rx.hstack(
                # Al cancelar, limpiar el id a eliminar para cerrar el diálogo controlado por estado
                rx.alert_dialog.cancel(rx.button("Cancelar", on_click=lambda _=None: AdminState.set_producto_a_eliminar(0))),
                rx.alert_dialog.action(rx.button("Confirmar", on_click=lambda _=None: AdminState.confirmar_eliminacion()))
            )
        ),
        open=AdminState.producto_id_a_eliminar != 0
    )

def crear_producto_dialog_component() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.trigger(
            PrimaryButton("Crear Producto", on_click=AdminState.abrir_modal_crear)
        ),
        rx.dialog.content(
            rx.flex(
                rx.dialog.title("Crear Producto"),
                crear_producto_form(),
                justify="center",
                align="center",
                direction="column"
            ),
            rx.flex(
                SecondaryButton("Cancelar", on_click=AdminState.cerrar_modal_crear),
                spacing="3",
                margin_top="16px",
                justify="center"
            ),
            style={"width": "400px"}
        ),
        open=AdminState.modal_crear_abierto,
        on_open_change=AdminState.set_modal_crear_abierto
    )

#edit 
def crear_producto_form() -> rx.Component:
    return rx.form(
        rx.vstack(
            rx.text("Nombre", font_weight="bold"),
            rx.input(name="nombre", placeholder="Nombre del producto", width="100%"),
            
            rx.text("Descripción", font_weight="bold"),
            rx.input(name="descripcion", placeholder="Descripción", width="100%"),
            
            rx.text("Precio", font_weight="bold"),
            rx.input(name="precio", type="number", step="0.01", placeholder="Precio", width="100%"),
            
            rx.text("Marca", font_weight="bold"),
            rx.input(name="marca", placeholder="Marca", width="100%"),
            
            rx.text("Categoría", font_weight="bold"),
            rx.input(name="categoria", placeholder="Categoría", width="100%"),
            
            rx.text("Talle", font_weight="bold"),
            rx.input(name="talle", placeholder="Talle", width="100%"),
            
            # 👇 Campo de imagen consistente
            rx.text("Imagen URL", font_weight="bold"),
            rx.input(name="imagen_url", placeholder="URL de la imagen", width="100%"),
            
            rx.text("Colores y stock", font_weight="bold"),
            rx.foreach(
                AdminState.colores,
                lambda c, i: rx.hstack(
                    rx.input(
                        placeholder="Color",
                        value=c.get("color", ""),
                        on_change=lambda v: AdminState.actualizar_color(i, v),
                    ),
                    rx.input(
                        type="number",
                        placeholder="Cantidad",
                        value=str(c.get("cantidad", 0)),
                        on_change=lambda v: AdminState.actualizar_cantidad(i, v),
                    )
                )
            ),
            rx.button("Agregar color", type="button", on_click=AdminState.agregar_color),

            rx.text(f"Cantidad total: {AdminState.cantidad_total}", font_weight="bold"),

            PrimaryButton("Guardar", type="submit", width="100%"),
            spacing="4",
            width="100%"
        ),
        on_submit=AdminState.crear_producto
    )

def editar_producto_dialog_component(producto: dict) -> rx.Component:
    return rx.dialog.root(
        rx.dialog.trigger(
            rx.button("Editar", color_scheme="blue", 
                      on_click=lambda _: AdminState.abrir_modal_editar(producto["id_producto"], producto))
        ),
        rx.dialog.content(
            rx.flex(
                rx.dialog.title(f"Editar Producto ID {producto['id_producto']}"),
                editar_producto_form_dynamic(),
                justify="center",
                align="center",
                direction="column"
            ),
            rx.flex(
                rx.button("Cancelar", on_click=AdminState.cerrar_modal_editar),
                spacing="3",
                margin_top="16px",
                justify="center"
            ),
            style={"width": "400px"}
        ),
        open=AdminState.modal_editar_abierto & (AdminState.producto_id_a_editar == producto["id_producto"]),
        on_open_change=AdminState.set_modal_editar_abierto
    )

def editar_producto_form_dynamic() -> rx.Component:
    return rx.form(
        rx.vstack(
            rx.text("Nombre", font_weight="bold"),
            rx.input(name="nombre", value=AdminState.datos_edicion.get("nombre", ""), width="100%"),
            
            rx.text("Descripción", font_weight="bold"),
            rx.input(name="descripcion", value=AdminState.datos_edicion.get("descripcion", ""), width="100%"),
            
            rx.text("Precio", font_weight="bold"),
            rx.input(name="precio", type="number", step="0.01", value=AdminState.datos_edicion.get("precio", ""), width="100%"),
            
            rx.text("Marca", font_weight="bold"),
            rx.input(name="marca", value=AdminState.datos_edicion.get("marca", ""), width="100%"),
            
            rx.text("Categoría", font_weight="bold"),
            rx.input(name="categoria", value=AdminState.datos_edicion.get("categoria", ""), width="100%"),
            
            rx.text("Talle", font_weight="bold"),
            rx.input(name="talle", value=AdminState.datos_edicion.get("talle", ""), width="100%"),
            
            # 👇 Campo de imagen consistente
            rx.text("Imagen URL", font_weight="bold"),
            rx.input(name="imagen_url", value=AdminState.datos_edicion.get("imagen_url", ""), width="100%"),
            
            rx.text("Colores y stock", font_weight="bold"),
            rx.foreach(
                AdminState.colores,
                lambda c, i: rx.hstack(
                    rx.input(
                        placeholder="Color",
                        value=c.get("color", ""),
                        on_change=lambda v: AdminState.actualizar_color(i, v),
                    ),
                    rx.input(
                        type="number",
                        placeholder="Cantidad",
                        value=str(c.get("cantidad", 0)),
                        on_change=lambda v: AdminState.actualizar_cantidad(i, v),
                    )
                )
            ),
            rx.button("Agregar color", type="button", on_click=AdminState.agregar_color),

            rx.text(f"Cantidad total: {AdminState.datos_edicion.get('cantidad_total', 0)}", font_weight="bold"),

            PrimaryButton("Guardar", type="submit", width="100%"),
            spacing="4",
            width="100%"
        ),
        on_submit=AdminState.enviar_edicion
    )