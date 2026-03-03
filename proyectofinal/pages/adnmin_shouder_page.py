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

    @rx.event
    def cargar_productos(self):
        productos = []
        for p in obtener_productos():
            d = p.dict()
            # agregar cantidad desde stock si existe
            try:
                cantidad = 0
                if getattr(p, 'stock', None):
                    cantidad = getattr(p.stock, 'cantidad_disponible', 0)
                d['cantidad'] = cantidad
            except Exception:
                d['cantidad'] = 0
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

            # Validar formato de campos con regex (evitar inputs vacíos o con caracteres no permitidos)
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
            cantidad_val = None
            if data.get("cantidad") is not None and data.get("cantidad") != "":
                try:
                    cantidad_val = int(data.get("cantidad"))
                except Exception:
                    cantidad_val = None

            crear_producto(
                nombre=data["nombre"],
                descripcion=data["descripcion"],
                precio=precio_val,
                marca=data["marca"],
                categoria=data["categoria"],
                talle=data["talle"],
                imagen=imagen_entrada,
                cantidad=cantidad_val,
            )
            self.cargar_productos()
            self.error_message = ""
            self.imagen_local = ""
            self.preview_data_url = ""
            self.modal_crear_abierto = False
            return rx.toast(" Producto creado correctamente")
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
            # Normalizar y filtrar valores vacíos sin asumir que todos son str
            cleaned: dict = {}
            for k, v in (data or {}).items():
                if v is None:
                    continue
                # intentamos limpiar strings, si no es string lo convertimos
                try:
                    s = v.strip()
                except Exception:
                    s = str(v).strip()
                if s != "":
                    # Guardar el valor original (no la cadena) para campos numéricos
                    cleaned[k] = v

            data = cleaned
            if "imagen" not in data and self.imagen_local:
                data["imagen"] = self.imagen_local
            # Validar campos editados con misma regex que creación
            pat = re.compile(r'^[A-Za-z0-9ÁÉÍÓÚáéíóúÑñÜü\s\-_,\.]{1,100}$')
            for campo in ("nombre", "marca", "categoria", "talle"):
                if campo in data:
                    val = (data.get(campo) or "").strip()
                    if val != "" and not pat.match(val):
                        self.error_message = f"{campo.capitalize()} contiene caracteres inválidos"
                        return

            actualizado = editar_producto(producto_id, data)
            if actualizado:
                self.cargar_productos()
                self.error_message = ""
                self.modal_editar_abierto = False
                return rx.toast(" Producto actualizado correctamente")
            else:
                self.error_message = " Producto no encontrado"
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error_message = f" Error al editar producto: {e}"
        finally:
            self.imagen_local = ""
            self.preview_data_url = ""

    @rx.event
    def enviar_edicion(self, data: dict):
        # usar el producto seleccionado actualmente
        self.editar_producto(self.producto_id_a_editar, data)

    @rx.event
    async def subir_imagen(self, files):
        import os, tempfile, base64, mimetypes, time
        if not files:
            return
        archivo = files[0]
        filename = getattr(archivo, "filename", None)
        # Obtener contenido según tipo entregado por Reflex
        if hasattr(archivo, "read"):
            contenido = await archivo.read()
        elif isinstance(archivo, (bytes, bytearray)):
            contenido = bytes(archivo)
            if not filename:
                filename = f"imagen_{int(time.time())}.bin"
        else:
            # último recurso: intentar acceder a 'file' o 'content'
            posible = getattr(archivo, "content", None)
            if isinstance(posible, (bytes, bytearray)):
                contenido = bytes(posible)
            else:
                # no soportado
                self.toast("No se pudo leer el archivo subido")
                return
            if not filename:
                filename = getattr(archivo, "name", f"imagen_{int(time.time())}.bin")

        # Asegurar nombre de archivo y extensión
        if not filename:
            filename = f"imagen_{int(time.time())}.jpg"
        else:
            base, ext = os.path.splitext(filename)
            if not ext:
                filename = f"{base}.jpg"

        destino = os.path.join(tempfile.gettempdir(), filename)
        with open(destino, "wb") as f:
            f.write(contenido)
        self.imagen_local = destino
        # generar data URL para previsualización
        mime, _ = mimetypes.guess_type(filename)
        mime = mime or "image/jpeg"
        b64 = base64.b64encode(contenido).decode("ascii")
        self.preview_data_url = f"data:{mime};base64,{b64}"
        return rx.toast(f"Imagen cargada: {os.path.basename(destino)}")

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


def table_productos() -> rx.Component:
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.column_header_cell("ID"),
                rx.table.column_header_cell("Nombre"),
                rx.table.column_header_cell("Imagen"),
                rx.table.column_header_cell("Precio"),
                rx.table.column_header_cell("Marca"),
                rx.table.column_header_cell("Talle"),
                rx.table.column_header_cell("Cantidad"),
                rx.table.column_header_cell("Acciones")
            )
        ),
        rx.table.body(
            rx.foreach(AdminState.productos, render_fila_producto)
        )
    )


def render_fila_producto(p: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(p["id_producto"]),
        rx.table.cell(p["nombre"]),
        rx.table.cell(
            rx.image(
                src=p.get("imagen", ""),
                alt=p.get("nombre", ""),
                width="56px",
                height="56px",
                border_radius="6px",
                object_fit="cover",
            )
        ),
        rx.table.cell(f"${p['precio']}"),
        rx.table.cell(p["marca"]),
        rx.table.cell(p.get("talle", "")),
        rx.table.cell(p.get("cantidad", 0)),
        rx.table.cell(
            rx.hstack(
                DangerButton("Eliminar", on_click=lambda _=None, pid=p["id_producto"]: AdminState.set_producto_a_eliminar(pid)),
                editar_producto_dialog_component(p)
            )
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


def crear_producto_form() -> rx.Component:
    return rx.form(
        rx.vstack(
            rx.text("Nombre", font_weight="bold"),
            rx.input(name="nombre", width="100%"),
            
            rx.text("Descripción", font_weight="bold"),
            rx.input(name="descripcion", width="100%"),
            
            rx.text("Precio", font_weight="bold"),
            rx.input(type="number", name="precio", min="0", step="0.01", width="100%"),
            
            rx.text("Marca", font_weight="bold"),
            rx.input(name="marca", width="100%"),
            
            rx.text("Categoría", font_weight="bold"),
            rx.input(name="categoria", width="100%"),
            
            rx.text("Talle", font_weight="bold"),
            rx.input(name="talle", width="100%"),
            
            rx.text("Cantidad", font_weight="bold"),
            rx.input(type="number", name="cantidad", min="0", step="1", width="100%"),
            
            rx.text("Imagen URL (opcional)", font_weight="bold"),
            rx.input(name="imagen", width="100%"),
            
            rx.text("Subir imagen desde tu PC", font_weight="bold"),
            rx.upload(
                rx.button("Seleccionar imagen", type="button", width="100%"),
                multiple=False,
                accept="image/*",
                on_drop=AdminState.subir_imagen,
            ),
            
            rx.cond(
                AdminState.imagen_local != "",
                rx.vstack(
                    rx.text("Imagen local lista para subir a Drive ✅"),
                    rx.cond(
                        AdminState.preview_data_url != "",
                        rx.image(
                            src=AdminState.preview_data_url,
                            width="160px",
                            height="160px",
                            border_radius="8px"
                        ),
                        rx.box()
                    )
                ),
                rx.box()
            ),
            
            # 👇 Botón unificado con el estilo de los demás
            PrimaryButton("Guardar", type="submit", width="100%"),
            spacing="4",
            width="100%"
        ),
        on_submit=AdminState.crear_producto
    )


def editar_producto_dialog_component(producto: dict) -> rx.Component:
    return rx.dialog.root(
        rx.dialog.trigger(
            SecondaryButton("Editar", on_click=lambda _=None, pid=producto["id_producto"], prod=producto: AdminState.abrir_modal_editar(pid, prod))
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
                SecondaryButton("Cancelar", on_click=AdminState.cerrar_modal_editar),
                spacing="3",
                margin_top="16px",
                justify="center"
            ),
            style={"width": "400px"}
        ),
        # Abrir sólo el diálogo del producto seleccionado
        open=(AdminState.modal_editar_abierto & (AdminState.producto_id_a_editar == producto["id_producto"])),
        on_open_change=AdminState.set_modal_editar_abierto
    )

def editar_producto_form(producto: dict) -> rx.Component:
    return rx.form(
        rx.vstack(
            rx.text("Nombre", font_weight="bold"),
            rx.input(name="nombre", default_value=producto.get("nombre", ""), width="100%"),
            
            rx.text("Descripción", font_weight="bold"),
            rx.input(name="descripcion", default_value=producto.get("descripcion", ""), width="100%"),
            
            rx.text("Precio", font_weight="bold"),
            rx.input(
                type="number",
                name="precio",
                min="0",
                step="0.01",
                default_value=str(producto.get("precio", "0.00")),
                width="100%"
            ),
            
            rx.text("Marca", font_weight="bold"),
            rx.input(name="marca", default_value=producto.get("marca", ""), width="100%"),
            
            rx.text("Categoría", font_weight="bold"),
            rx.input(name="categoria", default_value=producto.get("categoria", ""), width="100%"),
            
            rx.text("Talle", font_weight="bold"),
            rx.input(name="talle", default_value=producto.get("talle", ""), width="100%"),
            
            rx.text("Imagen URL", font_weight="bold"),
            rx.input(name="imagen", default_value=producto.get("imagen", ""), width="100%"),
            
            rx.text("Cantidad", font_weight="bold"),
            rx.input(
                type="number",
                name="cantidad",
                min="0",
                step="1",
                default_value=str(producto.get("cantidad", "0")),
                width="100%"
            ),
            
            PrimaryButton("Guardar", type="submit", width="100%"),
            spacing="4",
            width="100%"
        ),
        on_submit=AdminState.enviar_edicion
    )

def editar_producto_form_dynamic() -> rx.Component:
    # Formulario que toma valores desde AdminState.datos_edicion
    return rx.form(
        rx.vstack(
            rx.text("Nombre", font_weight="bold"),
            rx.input(name="nombre", default_value=AdminState.datos_edicion.get("nombre", ""), width="100%"),
            
            rx.text("Descripción", font_weight="bold"),
            rx.input(name="descripcion", default_value=AdminState.datos_edicion.get("descripcion", ""), width="100%"),
            
            rx.text("Precio", font_weight="bold"),
            rx.input(
                type="number",
                name="precio",
                min="0",
                step="0.01",
                default_value=str(AdminState.datos_edicion.get("precio", "0.00")),
                width="100%"
            ),
            
            rx.text("Marca", font_weight="bold"),
            rx.input(name="marca", default_value=AdminState.datos_edicion.get("marca", ""), width="100%"),
            
            rx.text("Categoría", font_weight="bold"),
            rx.input(name="categoria", default_value=AdminState.datos_edicion.get("categoria", ""), width="100%"),
            
            rx.text("Talle", font_weight="bold"),
            rx.input(name="talle", default_value=AdminState.datos_edicion.get("talle", ""), width="100%"),
            
            rx.text("Imagen URL", font_weight="bold"),
            rx.input(name="imagen", default_value=AdminState.datos_edicion.get("imagen", ""), width="100%"),
            
            rx.text("Cantidad", font_weight="bold"),
            rx.input(
                type="number",
                name="cantidad",
                min="0",
                step="1",
                default_value=str(AdminState.datos_edicion.get("cantidad", "0")),
                width="100%"
            ),
            
            PrimaryButton("Guardar", type="submit", width="100%"),
            spacing="4",
            width="100%"
        ),
        on_submit=AdminState.enviar_edicion
    )