"""Panel de productos del admin (T-050, D-028, D-049).

Tres pantallas, tres estados, ninguna comparte formulario: el listado filtra y
pagina; el alta crea el producto con sus variantes en un solo envio; la edicion
guarda los campos, edita las variantes fila por fila y da de baja el producto.

Los campos del producto viajan como datos del formulario (``rx.form``), asi que
un error de validacion muestra el mensaje al lado del campo y el navegador
conserva lo cargado. La imagen se sube aparte: el archivo se valida en el
servidor y lo que se guarda en la DB es la ruta.

Toda accion que escribe vuelve a pedir el rol (T-023): una sesion vencida con la
pagina abierta no cambia un producto.
"""

from __future__ import annotations

import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any

import reflex as rx
from sqlalchemy.exc import SQLAlchemyError

from app.service import imagen_servicio, producto_servicio
from app.service.producto_servicio import ErrorDeProducto
from app.state.admin_estado import AdminEstado
from app.state.parametros import id_de_la_url
from app.ui import Toast

logger = logging.getLogger(__name__)

MENSAJE_ERROR = "No pudimos cargar los productos. Proba de nuevo en unos segundos."
MENSAJE_AL_GUARDAR = "No pudimos guardar los cambios. Proba de nuevo en unos segundos."
RUTA_LISTA = "/admin/productos"


def _directorio_de_carga() -> Path:
    """Where Reflex keeps the uploads; the service only receives the path."""
    return Path(rx.get_upload_dir())


async def _leer_archivo(archivo: rx.UploadFile) -> tuple[str, bytes]:
    """Original name and bytes of one uploaded file."""
    return archivo.filename or "", await archivo.read()


def _errores_de(error: ErrorDeProducto) -> dict[str, str]:
    """Field errors keyed by input name; "formulario" is the page-level one."""
    return {error.campo or "formulario": error.mensaje}


class ProductosAdminEstado(AdminEstado):
    """Listado con filtro por estado, busqueda y paginacion (design.md 5)."""

    busqueda: str = ""
    filtro: str = producto_servicio.ESTADO_POR_DEFECTO
    pagina: int = 1
    productos: list[dict[str, Any]] = []
    total: int = 0
    total_paginas: int = 1

    filtros: list[dict[str, str]] = producto_servicio.opciones_de_estado()

    @rx.event
    async def on_load(self):
        return await self._iniciar()

    @rx.event
    async def reintentar(self):
        return await self._iniciar()

    @rx.var
    def vacio(self) -> bool:
        return not self.productos

    @rx.var
    def resumen(self) -> str:
        if self.total == 0:
            return "No hay productos con estos filtros."
        if self.total == 1:
            return "1 producto"
        return f"{self.total} productos"

    @rx.event
    def filtrar(self, valor: str):
        self.filtro = valor
        self.pagina = 1
        self._cargar()

    @rx.event
    def escribir_busqueda(self, texto: str) -> None:
        self.busqueda = texto

    @rx.event
    def buscar(self, datos: dict[str, Any]):
        self.busqueda = str(datos.get("busqueda", "") or "").strip()
        self.pagina = 1
        self._cargar()

    @rx.event
    def limpiar(self):
        self.filtro = producto_servicio.ESTADO_POR_DEFECTO
        self.busqueda = ""
        self.pagina = 1
        self._cargar()

    @rx.event
    def anterior(self):
        if self.pagina > 1:
            self.pagina -= 1
            self._cargar()

    @rx.event
    def siguiente(self):
        if self.pagina < self.total_paginas:
            self.pagina += 1
            self._cargar()

    def _cargar(self) -> None:
        try:
            resultado = producto_servicio.listar_para_admin(
                busqueda=self.busqueda,
                estado=self.filtro,
                pagina=self.pagina,
            )
        except SQLAlchemyError:
            logger.exception("Fallo el listado de productos del admin")
            self.error = MENSAJE_ERROR
            self.cargando = False
            return

        self.productos = [asdict(producto) for producto in resultado.productos]
        self.total = resultado.total
        self.pagina = resultado.pagina
        self.total_paginas = resultado.total_paginas
        self.filtro = resultado.filtro
        self.busqueda = resultado.busqueda
        self.cargando = False


class ProductoNuevoEstado(AdminEstado):
    """Alta de un producto con sus variantes iniciales (D-049)."""

    nombre: str = ""
    marca: str = ""
    precio: str = ""
    descripcion: str = ""
    categoria_id: str = ""
    categorias: list[dict[str, str]] = []
    errores: dict[str, str] = {}
    imagen: str = ""
    error_imagen: str = ""
    variantes: list[dict[str, Any]] = []
    nuevo_color: str = ""
    nuevo_talle: str = ""
    nuevo_cantidad: str = "1"
    error_variante: str = ""

    @rx.event
    async def on_load(self):
        return await self._iniciar()

    @rx.event
    async def reintentar(self):
        return await self._iniciar()

    @rx.var
    def hay_variantes(self) -> bool:
        return bool(self.variantes)

    @rx.var
    def resumen_variantes(self) -> str:
        total = len(self.variantes)
        if total == 1:
            return "1 variante"
        return f"{total} variantes"

    def _cargar(self) -> None:
        try:
            self.categorias = producto_servicio.categorias_para_formulario()
        except SQLAlchemyError:
            logger.exception("Fallo la carga de categorias del alta de producto")
            self.error = MENSAJE_ERROR
            self.cargando = False
            return

        self.cargando = False

    @rx.event
    async def subir_imagen(self, files: list[rx.UploadFile]):
        """Validate and store the image; the form only keeps the URL."""
        destino = await self._exigir_admin()
        if destino is not None:
            return destino

        if not files:
            self.error_imagen = imagen_servicio.MENSAJE_SIN_ARCHIVO
            return

        directorio = _directorio_de_carga()
        try:
            nombre, datos = await _leer_archivo(files[0])
            nueva = imagen_servicio.guardar(nombre, datos, directorio)
        except imagen_servicio.ErrorDeImagen as error:
            self.error_imagen = str(error)
            return
        except OSError:
            logger.exception("Fallo el guardado de la imagen del producto")
            self.error_imagen = "No pudimos guardar la imagen. Proba de nuevo."
            return

        # La anterior no llego a guardarse en la base: se puede borrar.
        imagen_servicio.borrar(self.imagen, directorio)
        self.imagen = nueva
        self.error_imagen = ""
        return Toast("Imagen cargada.")

    @rx.event
    def quitar_imagen(self):
        """Drop the pending image and its file: nothing points at it yet."""
        imagen_servicio.borrar(self.imagen, _directorio_de_carga())
        self.imagen = ""
        self.error_imagen = ""

    @rx.event
    def escribir_campo(self, campo: str, valor: str):
        """Controlled input: keep the value and drop its stale error."""
        setattr(self, campo, valor)
        if campo.startswith("nuevo_"):
            # El aviso de la fila repetida ya no aplica: se esta corrigiendo.
            self.error_variante = ""
        if campo in self.errores:
            self.errores = {
                clave: mensaje
                for clave, mensaje in self.errores.items()
                if clave != campo
            }

    @rx.event
    def agregar_variante(self):
        """Add a row to the pending list; validation matches the service."""
        try:
            fila = producto_servicio.validar_variante(
                self.nuevo_color,
                self.nuevo_talle,
                self.nuevo_cantidad,
            )
        except ErrorDeProducto as error:
            self.error_variante = error.mensaje
            return

        repetida = any(
            str(variante["color"]).lower() == str(fila["color"]).lower()
            and str(variante["talle"]).lower() == str(fila["talle"]).lower()
            for variante in self.variantes
        )
        if repetida:
            self.error_variante = (
                f"Ya agregaste {fila['color']} talle {fila['talle']}."
            )
            return

        self.variantes = [
            *self.variantes,
            {
                "color": fila["color"],
                "talle": fila["talle"],
                "cantidad": fila["cantidad"],
            },
        ]
        self.nuevo_color = ""
        self.nuevo_talle = ""
        self.nuevo_cantidad = "1"
        self.error_variante = ""

    @rx.event
    def quitar_variante(self, indice: int):
        """Drop a row that has not been saved yet."""
        self.variantes = [
            variante
            for posicion, variante in enumerate(self.variantes)
            if posicion != indice
        ]

    @rx.event
    async def guardar(self):
        """Create the product and its variants in one transaction."""
        destino = await self._exigir_admin()
        if destino is not None:
            return destino

        try:
            producto_id = producto_servicio.crear_producto(
                datos={
                    "nombre": self.nombre,
                    "marca": self.marca,
                    "precio": self.precio,
                    "descripcion": self.descripcion,
                    "categoria_id": self.categoria_id,
                    "imagen": self.imagen,
                },
                variantes=list(self.variantes),
                admin_id=self.admin_id,
            )
        except ErrorDeProducto as error:
            if error.campo == "variante":
                self.error_variante = error.mensaje
            else:
                self.errores = _errores_de(error)
            return
        except SQLAlchemyError:
            logger.exception("Fallo el alta de un producto")
            self.errores = {"formulario": MENSAJE_AL_GUARDAR}
            return

        self.errores = {}
        self.error_variante = ""
        return [
            Toast("Producto creado."),
            rx.redirect(f"{RUTA_LISTA}/{producto_id}"),
        ]


class ProductoEditarEstado(AdminEstado):
    """Edicion de un producto: campos, variantes por fila y baja logica."""

    producto_id: int = 0
    no_encontrado: bool = False
    nombre: str = ""
    marca: str = ""
    precio: str = ""
    descripcion: str = ""
    categoria_id: str = ""
    imagen: str = ""
    # Lo que hay en la base ahora mismo: sirve para borrar el archivo viejo
    # recien cuando el guardado lo reemplaza (si no se guarda, sigue en uso).
    imagen_guardada: str = ""
    activo: bool = True
    variantes: list[dict[str, Any]] = []
    categorias: list[dict[str, str]] = []
    errores: dict[str, str] = {}
    error_imagen: str = ""
    error_variante_id: int = 0
    error_variante: str = ""
    nuevo_color: str = ""
    nuevo_talle: str = ""
    nuevo_cantidad: str = "1"
    error_alta: str = ""

    @rx.event
    async def on_load(self):
        return await self._iniciar()

    @rx.event
    async def reintentar(self):
        return await self._iniciar()

    @rx.var
    def titulo(self) -> str:
        return self.nombre or "Producto"

    @rx.var
    def estado_etiqueta(self) -> str:
        return "Activo" if self.activo else "Inactivo"

    @rx.var
    def hay_variantes(self) -> bool:
        return bool(self.variantes)

    @rx.var
    def resumen_variantes(self) -> str:
        total = len(self.variantes)
        if total == 1:
            return "1 variante"
        return f"{total} variantes"

    def _cargar(self) -> None:
        self.no_encontrado = False
        self.error_variante_id = 0
        self.error_variante = ""
        self.error_alta = ""

        producto_id = id_de_la_url(self.router.url)
        if producto_id is None:
            self._marcar_no_encontrado()
            return

        try:
            detalle = producto_servicio.obtener_para_editar(producto_id)
        except SQLAlchemyError:
            logger.exception("Fallo la consulta del producto %s", producto_id)
            self.error = MENSAJE_ERROR
            self.cargando = False
            return

        if detalle is None:
            self._marcar_no_encontrado()
            return

        self.producto_id = detalle.id
        self.nombre = detalle.nombre
        self.marca = detalle.marca
        self.precio = detalle.precio
        self.descripcion = detalle.descripcion
        self.categoria_id = str(detalle.categoria_id)
        self.imagen = detalle.imagen
        self.imagen_guardada = detalle.imagen
        self.activo = detalle.activo
        self.categorias = detalle.categorias
        self.variantes = [
            {
                "id": variante.id,
                "color": variante.color,
                "talle": variante.talle,
                "cantidad": str(variante.cantidad),
            }
            for variante in detalle.variantes
        ]
        self.cargando = False

    def _marcar_no_encontrado(self) -> None:
        self.no_encontrado = True
        self.cargando = False
        self.variantes = []

    @rx.event
    async def subir_imagen(self, files: list[rx.UploadFile]):
        """Replace the image; the previous managed file is removed."""
        destino = await self._exigir_admin()
        if destino is not None:
            return destino

        if not files:
            self.error_imagen = imagen_servicio.MENSAJE_SIN_ARCHIVO
            return

        directorio = _directorio_de_carga()
        try:
            nombre, datos = await _leer_archivo(files[0])
            self.imagen = imagen_servicio.guardar(nombre, datos, directorio)
        except imagen_servicio.ErrorDeImagen as error:
            self.error_imagen = str(error)
            return
        except OSError:
            logger.exception("Fallo el guardado de la imagen del producto")
            self.error_imagen = "No pudimos guardar la imagen. Proba de nuevo."
            return

        self.error_imagen = ""
        return Toast("Imagen cargada.")

    @rx.event
    def quitar_imagen(self):
        """Only clears the field: the file is deleted when the form is saved."""
        self.imagen = ""
        self.error_imagen = ""

    @rx.event
    def escribir_campo(self, campo: str, valor: str):
        """Controlled input: keep the value and drop its stale error."""
        setattr(self, campo, valor)
        if campo.startswith("nuevo_"):
            # El aviso de la fila nueva ya no aplica: se esta corrigiendo.
            self.error_alta = ""
        if campo in self.errores:
            self.errores = {
                clave: mensaje
                for clave, mensaje in self.errores.items()
                if clave != campo
            }

    @rx.event
    async def guardar_campos(self):
        destino = await self._exigir_admin()
        if destino is not None:
            return destino

        try:
            producto_servicio.actualizar_producto(
                self.producto_id,
                datos={
                    "nombre": self.nombre,
                    "marca": self.marca,
                    "precio": self.precio,
                    "descripcion": self.descripcion,
                    "categoria_id": self.categoria_id,
                    "imagen": self.imagen,
                },
                admin_id=self.admin_id,
            )
        except ErrorDeProducto as error:
            self.errores = _errores_de(error)
            return
        except SQLAlchemyError:
            logger.exception("Fallo la edicion del producto %s", self.producto_id)
            self.errores = {"formulario": MENSAJE_AL_GUARDAR}
            return

        self.errores = {}
        self._cargar()
        return Toast("Cambios guardados.")

    @rx.event
    def escribir_variante(self, variante_id: int, campo: str, valor: str):
        """Keep the row inputs controlled while they are being edited."""
        self.variantes = [
            {**variante, campo: valor} if variante["id"] == variante_id else variante
            for variante in self.variantes
        ]

    @rx.event
    async def guardar_variante(self, variante_id: int):
        destino = await self._exigir_admin()
        if destino is not None:
            return destino

        fila = next(
            (
                variante
                for variante in self.variantes
                if variante["id"] == variante_id
            ),
            None,
        )
        if fila is None:
            return

        try:
            producto_servicio.actualizar_variante(
                self.producto_id,
                variante_id,
                color=fila["color"],
                talle=fila["talle"],
                cantidad=fila["cantidad"],
                admin_id=self.admin_id,
            )
        except ErrorDeProducto as error:
            self.error_variante_id = variante_id
            self.error_variante = error.mensaje
            return
        except SQLAlchemyError:
            logger.exception("Fallo el guardado de la variante %s", variante_id)
            self.error_variante_id = variante_id
            self.error_variante = MENSAJE_AL_GUARDAR
            return

        self._cargar()
        return Toast("Variante guardada.")

    @rx.event
    async def agregar_variante(self):
        destino = await self._exigir_admin()
        if destino is not None:
            return destino

        try:
            producto_servicio.agregar_variante(
                self.producto_id,
                color=self.nuevo_color,
                talle=self.nuevo_talle,
                cantidad=self.nuevo_cantidad,
                admin_id=self.admin_id,
            )
        except ErrorDeProducto as error:
            self.error_alta = error.mensaje
            return
        except SQLAlchemyError:
            logger.exception("Fallo el alta de una variante del producto %s", self.producto_id)
            self.error_alta = MENSAJE_AL_GUARDAR
            return

        self.nuevo_color = ""
        self.nuevo_talle = ""
        self.nuevo_cantidad = "1"
        self.error_alta = ""
        self._cargar()
        return Toast("Variante agregada.")

    @rx.event
    async def eliminar_variante(self, variante_id: int):
        destino = await self._exigir_admin()
        if destino is not None:
            return destino

        try:
            producto_servicio.eliminar_variante(
                self.producto_id,
                variante_id,
                admin_id=self.admin_id,
            )
        except ErrorDeProducto as error:
            self.error_variante_id = variante_id
            self.error_variante = error.mensaje
            return
        except SQLAlchemyError:
            logger.exception("Fallo el borrado de la variante %s", variante_id)
            self.error_variante_id = variante_id
            self.error_variante = MENSAJE_AL_GUARDAR
            return

        self._cargar()
        return Toast("Variante eliminada.")

    @rx.event
    async def desactivar(self):
        return await self._cambiar_activo(activo=False)

    @rx.event
    async def reactivar(self):
        return await self._cambiar_activo(activo=True)

    async def _cambiar_activo(self, *, activo: bool):
        destino = await self._exigir_admin()
        if destino is not None:
            return destino

        try:
            producto_servicio.cambiar_activo(
                self.producto_id,
                activo=activo,
                admin_id=self.admin_id,
            )
        except ErrorDeProducto as error:
            return Toast(error.mensaje, tone="error")
        except SQLAlchemyError:
            logger.exception("Fallo el cambio de estado del producto %s", self.producto_id)
            return Toast(MENSAJE_AL_GUARDAR, tone="error")

        self._cargar()
        return Toast("Producto reactivado." if activo else "Producto desactivado.")
