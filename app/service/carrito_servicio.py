"""Cart rules (T-040, D-002, D-008, D-022, D-004).

The cart lives in the database and only for a registered buyer: there is no guest
cart, so logging in never needs to merge anything (D-008). A line is a variant
``(producto, color, talle)`` with its own stock (D-009) and the only cap is that
stock, not an arbitrary maximum (D-022).

Totals are computed here once: the cart page, the checkout and the order all read
the same numbers, so a subtotal can never disagree with what the buyer pays
(D-003, T-032). Prices arrive formatted for the view and as ``Decimal`` for the
order.

Every function opens and closes its own session through the repository (D-033);
the state layer only calls these functions (T-062). The admin does not buy: the
mutations reject an admin account even when called directly (D-050).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.model.carrito_modelo import Carrito
from app.model.producto_modelo import Producto
from app.model.variante_modelo import Stocks
from app.repository import carrito_repositorio
from app.service.formato_moneda import formatear_precio
from app.service.sesion_servicio import MENSAJE_SOLO_COMPRADOR, usuario_puede_comprar

MENSAJE_VARIANTE = "Ese producto ya no esta disponible."
MENSAJE_LINEA = "Ese producto ya no esta en el carrito."
MENSAJE_CANTIDAD = "La cantidad minima es 1."

_CENTAVOS = Decimal("0.01")


class ErrorDeCarrito(ValueError):
    """Invalid quantity, unknown variant or not enough stock."""


@dataclass(frozen=True)
class LineaCarrito:
    """One cart line, ready to render and to hand over to the checkout."""

    id: int
    variante_id: int
    producto_id: int
    nombre: str
    marca: str
    color: str
    talle: str
    cantidad: int
    stock_disponible: int
    precio_unitario: str
    subtotal: str
    imagen: str
    precio_valor: Decimal


@dataclass(frozen=True)
class CarritoDeCompra:
    """The whole cart with the totals the page and the checkout share."""

    lineas: list[LineaCarrito]
    total_unidades: int
    subtotal: str
    subtotal_valor: Decimal

    @property
    def vacio(self) -> bool:
        return not self.lineas


def _exigir_comprador(usuario_id: int) -> None:
    """Reject the admin even when a cart action is invoked directly (D-050).

    The role is read from the database on every call: hiding the button in the
    product page is not the permission (D-021).
    """
    if not usuario_puede_comprar(usuario_id):
        raise ErrorDeCarrito(MENSAJE_SOLO_COMPRADOR)


def _cantidad_valida(cantidad: int) -> int:
    """Reject zero, negatives and anything that is not a whole number."""
    try:
        valor = int(cantidad)
    except (TypeError, ValueError) as error:
        raise ErrorDeCarrito(MENSAJE_CANTIDAD) from error
    if valor < 1:
        raise ErrorDeCarrito(MENSAJE_CANTIDAD)
    return valor


def _validar_stock(producto: Producto, variante: Stocks, cantidad: int) -> None:
    """Fail with the product name in the message, not with a silent no-op.

    "Falta stock" alone does not tell the buyer which size to change, so the
    message names the product, the colour, the size and what is left.
    """
    disponible = int(variante.cantidad_disponible)
    if cantidad <= disponible:
        return

    detalle = f"{producto.nombre} ({variante.color}, talle {variante.talle})"
    if disponible <= 0:
        raise ErrorDeCarrito(f"{detalle} no tiene stock.")
    raise ErrorDeCarrito(f"Solo quedan {disponible} unidades de {detalle}.")


def _a_linea(linea: Carrito, variante: Stocks, producto: Producto) -> LineaCarrito:
    cantidad = max(1, int(linea.cantidad))
    precio = Decimal(producto.precio)

    return LineaCarrito(
        id=linea.id_carrito or 0,
        variante_id=variante.id_stock or 0,
        producto_id=producto.id or 0,
        nombre=producto.nombre,
        marca=producto.marca,
        color=variante.color,
        talle=variante.talle,
        cantidad=cantidad,
        stock_disponible=int(variante.cantidad_disponible),
        precio_unitario=formatear_precio(precio),
        subtotal=formatear_precio(precio * cantidad),
        imagen=producto.imagen or "",
        precio_valor=precio.quantize(_CENTAVOS),
    )


def _armar(filas: list[tuple[Carrito, Stocks, Producto]]) -> CarritoDeCompra:
    """Sort the lines by name and add the totals once."""
    lineas = sorted(
        (_a_linea(*fila) for fila in filas),
        key=lambda item: (item.nombre.lower(), item.color, item.talle),
    )
    total_unidades = sum(linea.cantidad for linea in lineas)
    subtotal = sum(
        (linea.precio_valor * linea.cantidad for linea in lineas),
        Decimal("0"),
    ).quantize(_CENTAVOS)

    return CarritoDeCompra(
        lineas=lineas,
        total_unidades=total_unidades,
        subtotal=formatear_precio(subtotal),
        subtotal_valor=subtotal,
    )


def ver_carrito(usuario_id: int) -> CarritoDeCompra:
    """The user's cart as the page needs it, empty cart included."""
    return _armar(carrito_repositorio.listar_lineas(usuario_id))


def contar_unidades(usuario_id: int) -> int:
    """Units in the cart, for the header badge (T-078).

    A read, not a purchase action: the caller decides who sees the number, and
    the admin's cart is always empty anyway (D-050).
    """
    return carrito_repositorio.contar_unidades(usuario_id)


def agregar(usuario_id: int, variante_id: int, cantidad: int = 1) -> CarritoDeCompra:
    """Add units of a variant, adding up when the line already exists (D-022).

    The stock check counts what is already in the cart: asking for 2 twice with
    3 units on the shelf must fail the second time instead of hiding an overrun.
    """
    _exigir_comprador(usuario_id)
    cantidad = _cantidad_valida(cantidad)

    encontrada = carrito_repositorio.obtener_variante(variante_id)
    if encontrada is None:
        raise ErrorDeCarrito(MENSAJE_VARIANTE)
    variante, producto = encontrada
    if not producto.activo:
        raise ErrorDeCarrito(MENSAJE_VARIANTE)

    linea = carrito_repositorio.obtener_linea(usuario_id, variante_id)
    actual = int(linea.cantidad) if linea is not None else 0
    _validar_stock(producto, variante, actual + cantidad)

    if linea is None:
        carrito_repositorio.crear_linea(
            usuario_id=usuario_id,
            variante_id=variante_id,
            cantidad=cantidad,
        )
    else:
        carrito_repositorio.actualizar_cantidad(
            linea_id=linea.id_carrito or 0,
            cantidad=actual + cantidad,
        )

    return ver_carrito(usuario_id)


def cambiar_cantidad(
    usuario_id: int,
    linea_id: int,
    cantidad: int,
) -> CarritoDeCompra:
    """Set the quantity of a line, scoped to its owner and capped by stock."""
    _exigir_comprador(usuario_id)
    cantidad = _cantidad_valida(cantidad)

    linea = carrito_repositorio.obtener_linea_por_id(usuario_id, linea_id)
    if linea is None:
        raise ErrorDeCarrito(MENSAJE_LINEA)

    encontrada = carrito_repositorio.obtener_variante(linea.variante_id)
    if encontrada is None:
        raise ErrorDeCarrito(MENSAJE_VARIANTE)
    variante, producto = encontrada
    if not producto.activo:
        raise ErrorDeCarrito(MENSAJE_VARIANTE)

    _validar_stock(producto, variante, cantidad)
    carrito_repositorio.actualizar_cantidad(linea_id=linea_id, cantidad=cantidad)
    return ver_carrito(usuario_id)


def quitar(usuario_id: int, linea_id: int) -> CarritoDeCompra:
    """Remove a line; a line from another cart is ignored, not deleted."""
    _exigir_comprador(usuario_id)
    linea = carrito_repositorio.obtener_linea_por_id(usuario_id, linea_id)
    if linea is not None:
        carrito_repositorio.borrar_linea(linea_id)
    return ver_carrito(usuario_id)


def vaciar(usuario_id: int) -> CarritoDeCompra:
    """Empty the cart."""
    _exigir_comprador(usuario_id)
    carrito_repositorio.vaciar(usuario_id)
    return ver_carrito(usuario_id)
