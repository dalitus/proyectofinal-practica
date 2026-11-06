"""CRUD de productos y variantes para el panel (T-050, D-009, D-015, D-023,
D-028, D-049).

El servicio concentra las reglas: largos y formato de cada campo, precio en
pesos enteros, combinacion `(color, talle)` unica por producto y borrado logico
del producto. El repositorio solo escribe; el estado solo guarda lo que la
pagina pinta.

Cada escritura se audita (D-031) despues de confirmar la transaccion: si la base
rechaza el cambio, no hay nada que registrar.

Los mensajes son de formulario: se muestran al lado del campo, no como error de
pagina, y nunca traen el texto crudo de MySQL.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal

from app.model.producto_modelo import Producto
from app.repository import producto_repositorio
from app.repository.producto_repositorio import (
    ProductoNoEncontrado,
    VarianteDuplicada,
    VarianteEnUso,
    VarianteNoEncontrada,
)
from app.service.auditoria import registrar as registrar_auditoria
from app.service.formato_moneda import formatear_precio

PRODUCTOS_POR_PAGINA = 10

# Valor del filtro -> etiqueta del select. "todos" es el unico que no filtra.
FILTROS_DE_ESTADO: dict[str, str] = {
    "activos": "Activos",
    "inactivos": "Inactivos",
    "todos": "Todos",
}

ESTADO_POR_DEFECTO = "activos"

# Largos de las columnas `VARCHAR(255)`. Validar antes evita el error 1406 de
# MySQL, que corta la escritura en vez de truncar.
LARGO_NOMBRE = 120
LARGO_MARCA = 80
LARGO_DESCRIPCION = 255
LARGO_COLOR = 40
LARGO_TALLE = 20
LARGO_IMAGEN = 255

# La columna `productos.precio` es DECIMAL(10,0): pesos enteros.
PRECIO_MAXIMO = Decimal("99999999")

MENSAJES = {
    "nombre": "Pone el nombre del producto.",
    "marca": "Pone la marca.",
    "precio": "Pone un precio.",
    "categoria_id": "Elegi una categoria.",
    "color": "Pone el color.",
    "talle": "Pone el talle.",
    "cantidad": "Pone una cantidad valida (0 o mas).",
}


class ErrorDeProducto(ValueError):
    """Invalid data; ``campo`` says which input shows the message."""

    def __init__(
        self,
        mensaje: str,
        *,
        campo: str = "",
        variante_id: int = 0,
    ) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.campo = campo
        self.variante_id = variante_id


@dataclass(frozen=True)
class ProductoEnPanel:
    """One row of the admin product list, ready to render."""

    id: int
    nombre: str
    marca: str
    categoria: str
    precio: str
    activo: bool
    estado_etiqueta: str
    variantes: int
    stock: int


@dataclass(frozen=True)
class PaginaDeProductos:
    productos: list[ProductoEnPanel]
    total: int
    pagina: int
    total_paginas: int
    filtro: str
    busqueda: str


@dataclass(frozen=True)
class VarianteEnPanel:
    """One editable variant row: the combination and its own stock (D-009)."""

    id: int
    color: str
    talle: str
    cantidad: int


@dataclass(frozen=True)
class DetalleDeProducto:
    """The edit form and the variant rows of one product."""

    id: int
    nombre: str
    descripcion: str
    marca: str
    precio: str
    categoria_id: int
    imagen: str
    activo: bool
    variantes: list[VarianteEnPanel]
    categorias: list[dict[str, str]]


def _limpiar(valor: object) -> str:
    return str(valor or "").strip()


def _a_entero(valor: object, *, campo: str) -> int:
    texto = _limpiar(valor)
    if not texto:
        raise ErrorDeProducto(MENSAJES[campo], campo=campo)
    try:
        return int(texto)
    except ValueError as error:
        raise ErrorDeProducto(MENSAJES[campo], campo=campo) from error


def _a_precio(valor: object) -> Decimal:
    """Parse the price input as whole pesos.

    The column is ``DECIMAL(10,0)``: accepting cents would let MySQL round the
    amount without telling anyone, so a decimal is rejected with the reason.
    """
    texto = _limpiar(valor).replace(" ", "")
    if not texto:
        raise ErrorDeProducto(MENSAJES["precio"], campo="precio")
    if "," in texto:
        raise ErrorDeProducto(
            "El precio va en pesos enteros, sin centavos.",
            campo="precio",
        )

    # Un punto solo vale como separador de miles ("45.000"): si el ultimo grupo
    # no tiene tres digitos, era un decimal y no se redondea en silencio.
    if "." in texto:
        grupos = texto.split(".")
        valido = (
            1 <= len(grupos[0]) <= 3
            and all(len(grupo) == 3 and grupo.isdigit() for grupo in grupos[1:])
        )
        if not valido:
            raise ErrorDeProducto(
                "El precio va en pesos enteros, sin centavos.",
                campo="precio",
            )

    limpio = texto.replace(".", "")
    if not limpio.isdigit():
        raise ErrorDeProducto(
            "El precio va solo con numeros, en pesos enteros.",
            campo="precio",
        )

    monto = Decimal(limpio)
    if monto <= 0:
        raise ErrorDeProducto("El precio tiene que ser mayor a cero.", campo="precio")
    if monto > PRECIO_MAXIMO:
        raise ErrorDeProducto("El precio es demasiado alto.", campo="precio")
    return monto


def _texto_de_precio(valor: Decimal) -> str:
    """Editable text of a stored amount: ``45000``, never ``45000.00``."""
    entero = int(valor)
    return str(entero)


def opciones_de_estado() -> list[dict[str, str]]:
    return [
        {"valor": valor, "texto": etiqueta}
        for valor, etiqueta in FILTROS_DE_ESTADO.items()
    ]


def categorias_para_formulario() -> list[dict[str, str]]:
    """Every category, even the empty ones: the form is not the catalog."""
    return [
        {"valor": str(categoria.id), "texto": categoria.nombre}
        for categoria in producto_repositorio.listar_todas_las_categorias()
    ]


def _a_producto_en_panel(producto: Producto) -> ProductoEnPanel:
    variantes = list(producto.stocks)
    return ProductoEnPanel(
        id=producto.id or 0,
        nombre=producto.nombre,
        marca=producto.marca,
        categoria=producto.categoria.nombre if producto.categoria else "",
        precio=formatear_precio(producto.precio),
        activo=producto.activo,
        estado_etiqueta="Activo" if producto.activo else "Inactivo",
        variantes=len(variantes),
        stock=sum(variante.cantidad_disponible for variante in variantes),
    )


def listar_para_admin(
    *,
    busqueda: str = "",
    estado: str = ESTADO_POR_DEFECTO,
    pagina: int = 1,
) -> PaginaDeProductos:
    """One page of the panel list, with the same clamping as the catalog."""
    filtro = estado if estado in FILTROS_DE_ESTADO else ESTADO_POR_DEFECTO
    texto = _limpiar(busqueda)

    total = producto_repositorio.contar_para_admin(busqueda=texto, estado=filtro)
    total_paginas = max(1, math.ceil(total / PRODUCTOS_POR_PAGINA))
    pagina_actual = min(max(1, pagina), total_paginas)

    filas = producto_repositorio.listar_para_admin(
        busqueda=texto,
        estado=filtro,
        limite=PRODUCTOS_POR_PAGINA,
        offset=(pagina_actual - 1) * PRODUCTOS_POR_PAGINA,
    )

    return PaginaDeProductos(
        productos=[_a_producto_en_panel(fila) for fila in filas],
        total=total,
        pagina=pagina_actual,
        total_paginas=total_paginas,
        filtro=filtro,
        busqueda=texto,
    )


def obtener_para_editar(producto_id: int) -> DetalleDeProducto | None:
    """The edit form data, active or not; ``None`` when the id does not exist."""
    producto = producto_repositorio.obtener_para_editar(producto_id)
    if producto is None:
        return None

    return DetalleDeProducto(
        id=producto.id or 0,
        nombre=producto.nombre,
        descripcion=producto.descripcion,
        marca=producto.marca,
        precio=_texto_de_precio(producto.precio),
        categoria_id=producto.categoria_id,
        imagen=producto.imagen or "",
        activo=producto.activo,
        variantes=[
            VarianteEnPanel(
                id=variante.id_stock or 0,
                color=variante.color,
                talle=variante.talle,
                cantidad=variante.cantidad_disponible,
            )
            for variante in sorted(
                producto.stocks,
                key=lambda variante: (variante.color, variante.talle),
            )
        ],
        categorias=categorias_para_formulario(),
    )


def _validar_campos(
    datos: dict[str, object],
    *,
    categorias: set[int],
) -> dict[str, object]:
    """Normalise the product fields or fail with the first problem.

    Each branch names its field so the form can paint the message under that
    input without losing what the admin already typed.
    """
    nombre = _limpiar(datos.get("nombre"))
    if not nombre:
        raise ErrorDeProducto(MENSAJES["nombre"], campo="nombre")
    if len(nombre) > LARGO_NOMBRE:
        raise ErrorDeProducto(
            f"El nombre no puede superar los {LARGO_NOMBRE} caracteres.",
            campo="nombre",
        )

    marca = _limpiar(datos.get("marca"))
    if not marca:
        raise ErrorDeProducto(MENSAJES["marca"], campo="marca")
    if len(marca) > LARGO_MARCA:
        raise ErrorDeProducto(
            f"La marca no puede superar los {LARGO_MARCA} caracteres.",
            campo="marca",
        )

    descripcion = _limpiar(datos.get("descripcion"))
    if len(descripcion) > LARGO_DESCRIPCION:
        raise ErrorDeProducto(
            f"La descripcion no puede superar los {LARGO_DESCRIPCION} caracteres.",
            campo="descripcion",
        )

    imagen = _limpiar(datos.get("imagen"))
    if len(imagen) > LARGO_IMAGEN:
        raise ErrorDeProducto("La ruta de la imagen es demasiado larga.", campo="imagen")

    precio = _a_precio(datos.get("precio"))

    categoria_id = _a_entero(datos.get("categoria_id"), campo="categoria_id")
    if categoria_id not in categorias:
        raise ErrorDeProducto(
            "Esa categoria no existe. Recarga la pagina.",
            campo="categoria_id",
        )

    return {
        "nombre": nombre,
        "descripcion": descripcion,
        "marca": marca,
        "precio": precio,
        "categoria_id": categoria_id,
        "imagen": imagen or None,
    }


def validar_campos(datos: dict[str, object]) -> dict[str, object]:
    """Public wrapper: validate the form before the page saves anything."""
    return _validar_campos(datos, categorias=_ids_de_categoria())


def _ids_de_categoria() -> set[int]:
    return {
        int(categoria["valor"]) for categoria in categorias_para_formulario()
    }


def _validar_variante(color: object, talle: object, cantidad: object) -> dict[str, object]:
    """One variant row: colour, size and a whole non-negative stock."""
    color_limpio = _limpiar(color)
    if not color_limpio:
        raise ErrorDeProducto(MENSAJES["color"], campo="color")
    if len(color_limpio) > LARGO_COLOR:
        raise ErrorDeProducto(
            f"El color no puede superar los {LARGO_COLOR} caracteres.",
            campo="color",
        )

    talle_limpio = _limpiar(talle)
    if not talle_limpio:
        raise ErrorDeProducto(MENSAJES["talle"], campo="talle")
    if len(talle_limpio) > LARGO_TALLE:
        raise ErrorDeProducto(
            f"El talle no puede superar los {LARGO_TALLE} caracteres.",
            campo="talle",
        )

    cantidad_entera = _a_entero(cantidad, campo="cantidad")
    if cantidad_entera < 0:
        raise ErrorDeProducto(MENSAJES["cantidad"], campo="cantidad")

    return {"color": color_limpio, "talle": talle_limpio, "cantidad": cantidad_entera}


def validar_variante(color: object, talle: object, cantidad: object) -> dict[str, object]:
    return _validar_variante(color, talle, cantidad)


def _sin_repetidas(variantes: list[dict[str, object]]) -> None:
    """The unique index covers the database; this covers the same form twice."""
    vistas: set[tuple[str, str]] = set()
    for variante in variantes:
        clave = (str(variante["color"]).lower(), str(variante["talle"]).lower())
        if clave in vistas:
            raise ErrorDeProducto(
                f"Ya hay una variante {variante['color']} talle {variante['talle']}.",
                campo="variante",
            )
        vistas.add(clave)


def crear_producto(
    *,
    datos: dict[str, object],
    variantes: list[dict[str, object]],
    admin_id: int | None = None,
) -> int:
    """Create the product with its variants in one transaction (D-049)."""
    campos = validar_campos(datos)

    filas = [
        _validar_variante(
            variante.get("color"),
            variante.get("talle"),
            variante.get("cantidad"),
        )
        for variante in variantes
    ]
    _sin_repetidas(filas)

    if not filas:
        raise ErrorDeProducto(
            "Agrega al menos una variante con color, talle y stock.",
            campo="variante",
        )

    try:
        producto_id = producto_repositorio.crear_producto(campos, filas)
    except VarianteDuplicada as error:
        raise ErrorDeProducto(
            "Esa combinacion de color y talle ya existe en el producto.",
            campo="variante",
        ) from error

    registrar_auditoria(
        accion="crear_producto",
        entidad="producto",
        entidad_id=producto_id,
        admin_id=admin_id,
        detalle=f"{campos['nombre']} ({len(filas)} variantes)",
    )
    return producto_id


def actualizar_producto(
    producto_id: int,
    *,
    datos: dict[str, object],
    admin_id: int | None = None,
) -> None:
    """Save the product fields; the variants have their own actions."""
    campos = validar_campos(datos)

    try:
        producto_repositorio.actualizar_producto(producto_id, campos)
    except ProductoNoEncontrado as error:
        raise ErrorDeProducto("Ese producto ya no existe.") from error

    registrar_auditoria(
        accion="actualizar_producto",
        entidad="producto",
        entidad_id=producto_id,
        admin_id=admin_id,
        detalle=str(campos["nombre"]),
    )


def agregar_variante(
    producto_id: int,
    *,
    color: object,
    talle: object,
    cantidad: object,
    admin_id: int | None = None,
) -> None:
    """Add one variant row, rejecting a repeated combination first (D-009)."""
    fila = _validar_variante(color, talle, cantidad)

    if (
        producto_repositorio.variante_por_combinacion(
            producto_id,
            str(fila["color"]),
            str(fila["talle"]),
        )
        is not None
    ):
        raise ErrorDeProducto(
            f"Ya hay una variante {fila['color']} talle {fila['talle']}.",
            campo="variante",
        )

    try:
        producto_repositorio.agregar_variante(
            producto_id,
            color=str(fila["color"]),
            talle=str(fila["talle"]),
            cantidad=int(fila["cantidad"]),  # type: ignore[arg-type]
        )
    except ProductoNoEncontrado as error:
        raise ErrorDeProducto("Ese producto ya no existe.") from error
    except VarianteDuplicada as error:
        raise ErrorDeProducto(
            "Esa combinacion de color y talle ya existe en el producto.",
            campo="variante",
        ) from error

    registrar_auditoria(
        accion="agregar_variante",
        entidad="producto",
        entidad_id=producto_id,
        admin_id=admin_id,
        detalle=f"{fila['color']} / {fila['talle']} / {fila['cantidad']}",
    )


def actualizar_variante(
    producto_id: int,
    variante_id: int,
    *,
    color: object,
    talle: object,
    cantidad: object,
    admin_id: int | None = None,
) -> None:
    """Save one variant row; the error carries its id so the row paints it."""
    try:
        fila = _validar_variante(color, talle, cantidad)
    except ErrorDeProducto as error:
        error.variante_id = variante_id
        raise

    repetida = producto_repositorio.variante_por_combinacion(
        producto_id,
        str(fila["color"]),
        str(fila["talle"]),
        excluir_id=variante_id,
    )
    if repetida is not None:
        raise ErrorDeProducto(
            f"Ya hay una variante {fila['color']} talle {fila['talle']}.",
            campo="variante",
            variante_id=variante_id,
        )

    try:
        producto_repositorio.actualizar_variante(
            producto_id,
            variante_id,
            color=str(fila["color"]),
            talle=str(fila["talle"]),
            cantidad=int(fila["cantidad"]),  # type: ignore[arg-type]
        )
    except VarianteNoEncontrada as error:
        raise ErrorDeProducto(
            "Esa variante ya no existe. Recarga la pagina.",
            campo="variante",
        ) from error
    except VarianteDuplicada as error:
        raise ErrorDeProducto(
            "Esa combinacion de color y talle ya existe en el producto.",
            campo="variante",
            variante_id=variante_id,
        ) from error

    registrar_auditoria(
        accion="actualizar_variante",
        entidad="producto",
        entidad_id=producto_id,
        admin_id=admin_id,
        detalle=f"variante {variante_id}: {fila['color']} / {fila['talle']} / {fila['cantidad']}",
    )


def eliminar_variante(
    producto_id: int,
    variante_id: int,
    *,
    admin_id: int | None = None,
) -> None:
    """Delete a variant that no cart or order references (D-029)."""
    try:
        producto_repositorio.eliminar_variante(producto_id, variante_id)
    except VarianteNoEncontrada as error:
        raise ErrorDeProducto("Esa variante ya no existe. Recarga la pagina.") from error
    except VarianteEnUso as error:
        raise ErrorDeProducto(
            "Esa variante tiene pedidos o esta en un carrito: dejala con stock 0 "
            "en vez de borrarla.",
            variante_id=variante_id,
        ) from error

    registrar_auditoria(
        accion="eliminar_variante",
        entidad="producto",
        entidad_id=producto_id,
        admin_id=admin_id,
        detalle=f"variante {variante_id}",
    )


def cambiar_activo(
    producto_id: int,
    *,
    activo: bool,
    admin_id: int | None = None,
) -> None:
    """Soft delete or reactivate the product (D-028); the variants stay."""
    try:
        producto_repositorio.cambiar_activo(producto_id, activo=activo)
    except ProductoNoEncontrado as error:
        raise ErrorDeProducto("Ese producto ya no existe.") from error

    registrar_auditoria(
        accion="reactivar_producto" if activo else "desactivar_producto",
        entidad="producto",
        entidad_id=producto_id,
        admin_id=admin_id,
        detalle="activo" if activo else "inactivo",
    )


def desactivar_producto(producto_id: int, *, admin_id: int | None = None) -> None:
    """Name the action as the admin sees it: it is a soft delete."""
    cambiar_activo(producto_id, activo=False, admin_id=admin_id)


def reactivar_producto(producto_id: int, *, admin_id: int | None = None) -> None:
    cambiar_activo(producto_id, activo=True, admin_id=admin_id)
