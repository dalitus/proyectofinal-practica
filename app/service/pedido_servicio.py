"""Checkout rules and order lifecycle (T-043, T-044, D-005, D-010, D-032).

The checkout is a page, not a wizard (D-032) and there is no online payment: the
order is registered and the shipment is coordinated afterwards, so the total is
the cart subtotal with no shipping fee (D-005).

The total is never taken from the form: it is recomputed here from the cart and
the same ``Decimal`` the cart showed, so a tampered page cannot change what the
buyer pays (D-003, T-032).

The order lifecycle also lives here: ``TRANSICIONES`` is the only place that
knows which changes are legal, and cancelling is the only one that gives stock
back (D-010). The repository just locks the row and writes.

Each public function opens and closes its own session through the repository
(D-033); the state layer only calls these functions (T-062).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime

from app.model.perfil_modelo import UserProfile
from app.repository import pedido_repositorio
from app.repository.pedido_repositorio import (
    EstadoCambiado,
    PedidoNoEncontrado,
    StockInsuficiente,
)
from app.service import carrito_servicio
from app.service.auditoria import registrar as registrar_auditoria
from app.service.formato_moneda import formatear_precio


class ErrorDePedido(ValueError):
    """Invalid delivery data, empty cart, missing stock or a bad state change."""


@dataclass(frozen=True)
class DatosDeEntrega:
    """What the order stores about where it goes (D-005)."""

    direccion: str
    numero: str
    departamento: str
    codigo_postal: str
    ciudad: str
    provincia: str

    def como_dict(self) -> dict[str, str]:
        return {
            "direccion": self.direccion,
            "numero": self.numero,
            "departamento": self.departamento,
            "codigo_postal": self.codigo_postal,
            "ciudad": self.ciudad,
            "provincia": self.provincia,
        }


# Campo -> texto del error. Los cuatro primeros son obligatorios: el resto es
# opcional y se guarda tal cual.
MENSAJES_OBLIGATORIOS = {
    "direccion": "Pone tu direccion.",
    "numero": "Pone el numero.",
    "ciudad": "Pone tu ciudad.",
    "provincia": "Pone tu provincia.",
}


def _limpiar(valor: object) -> str:
    return str(valor or "").strip()


def errores_de_entrega(datos: dict[str, object]) -> dict[str, str]:
    """Per-field errors so the page can paint them next to each input (design.md 5)."""
    return {
        campo: mensaje
        for campo, mensaje in MENSAJES_OBLIGATORIOS.items()
        if not _limpiar(datos.get(campo))
    }


def validar_entrega(datos: dict[str, object]) -> DatosDeEntrega:
    """Normalise the form data or fail with the first missing field."""
    faltantes = errores_de_entrega(datos)
    if faltantes:
        raise ErrorDePedido("Completa los datos de entrega.")

    return DatosDeEntrega(
        direccion=_limpiar(datos.get("direccion")),
        numero=_limpiar(datos.get("numero")),
        departamento=_limpiar(datos.get("departamento")),
        codigo_postal=_limpiar(datos.get("codigo_postal")),
        ciudad=_limpiar(datos.get("ciudad")),
        provincia=_limpiar(datos.get("provincia")),
    )


def _mensaje_de_stock(error: StockInsuficiente) -> str:
    """Name the variant that failed: "falta stock" alone does not help."""
    if not error.nombre:
        return "Uno de los productos ya no esta disponible. Revisa el carrito."

    detalle = f"{error.nombre} ({error.color}, talle {error.talle})"
    if error.disponible <= 0:
        return f"{detalle} se quedo sin stock. Quitalo del carrito para seguir."
    return f"Quedan {error.disponible} unidades de {detalle}. Ajusta la cantidad."


def confirmar_pedido(usuario_id: int, entrega: DatosDeEntrega) -> int:
    """Create the order from the cart and return its number.

    The cart is read again here: the checkout always sells what is in the
    database now, not what the page rendered minutes ago (D-004).
    """
    carrito = carrito_servicio.ver_carrito(usuario_id)
    if carrito.vacio:
        raise ErrorDePedido("Tu carrito esta vacio.")

    lineas = [
        {
            "variante_id": linea.variante_id,
            "cantidad": linea.cantidad,
            "color": linea.color,
            "talle": linea.talle,
            "precio_unitario": linea.precio_valor,
        }
        for linea in carrito.lineas
    ]

    try:
        return pedido_repositorio.crear_pedido(
            usuario_id=usuario_id,
            lineas=lineas,
            entrega=entrega.como_dict(),
            total=carrito.subtotal_valor,
        )
    except StockInsuficiente as error:
        raise ErrorDePedido(_mensaje_de_stock(error)) from error


# --------------------------------------------------------------------------
# Ciclo de vida del pedido (T-044, D-010)
# --------------------------------------------------------------------------

# Los cuatro estados que existen. El admin filtra por estos mismos valores.
ESTADO_INICIAL = "en espera"
ESTADOS_DE_PEDIDO = (ESTADO_INICIAL, "enviado", "entregado", "cancelado")

# Unico lugar que conoce las transiciones validas. Entregado y cancelado son
# finales: no vuelven atras.
TRANSICIONES: dict[str, tuple[str, ...]] = {
    "en espera": ("enviado", "cancelado"),
    "enviado": ("entregado", "cancelado"),
    "entregado": (),
    "cancelado": (),
}

# Un pedido terminado no se puede tocar: se explica asi en vez de listar destinos.
MENSAJE_ESTADO_FINAL = "El pedido ya esta {estado} y no se puede cambiar."


def _mensaje_de_transicion(actual: str, nuevo: str) -> str:
    """Explain why the change is refused, naming both states."""
    if not TRANSICIONES.get(actual):
        return MENSAJE_ESTADO_FINAL.format(estado=actual)
    return f"No se puede pasar de '{actual}' a '{nuevo}'."


def cambiar_estado(pedido_id: int, nuevo: str, *, admin_id: int | None = None) -> str:
    """Apply one valid transition and return the new state (D-010).

    Only the admin panel calls this; the buyer never changes the state, it only
    reads it. Cancelling is not special-cased here: it goes through the same
    table and the repository restores the stock (D-010).
    """
    if nuevo not in ESTADOS_DE_PEDIDO:
        raise ErrorDePedido(f"El estado '{nuevo}' no existe.")

    try:
        actual = pedido_repositorio.obtener_estado(pedido_id)
    except PedidoNoEncontrado as error:
        raise ErrorDePedido(f"No existe el pedido #{pedido_id}.") from error

    if nuevo not in TRANSICIONES.get(actual, ()):
        raise ErrorDePedido(_mensaje_de_transicion(actual, nuevo))

    ahora = datetime.now()
    try:
        pedido_repositorio.cambiar_estado(
            pedido_id=pedido_id,
            estado_esperado=actual,
            estado_nuevo=nuevo,
            fecha_entrega=ahora if nuevo == "entregado" else None,
            fecha_cancelacion=ahora if nuevo == "cancelado" else None,
            reponer_stock=nuevo == "cancelado",
        )
    except PedidoNoEncontrado as error:
        raise ErrorDePedido(f"No existe el pedido #{pedido_id}.") from error
    except EstadoCambiado as error:
        raise ErrorDePedido(
            f"El pedido ya no esta en '{error.estado_esperado}': "
            f"ahora esta en '{error.estado_actual}'. Recarga la lista."
        ) from error

    # D-031: cancelar es su propia accion en el log, no un cambio mas.
    registrar_auditoria(
        accion="cancelar_pedido" if nuevo == "cancelado" else "cambiar_estado",
        entidad="pedido",
        entidad_id=pedido_id,
        admin_id=admin_id,
        detalle=f"{actual} -> {nuevo}",
    )

    return nuevo


def cancelar_pedido(pedido_id: int, *, admin_id: int | None = None) -> str:
    """Cancel the order and restore its stock (D-010).

    Kept as its own name so the admin action reads as what it is; the rule and
    the transaction are the same as ``cambiar_estado``.
    """
    return cambiar_estado(pedido_id, "cancelado", admin_id=admin_id)


# --------------------------------------------------------------------------
# Panel del admin: listado y detalle (T-051, D-030)
# --------------------------------------------------------------------------

PEDIDOS_POR_PAGINA = 10

# Etiqueta visible de cada estado. Las claves salen de ESTADOS_DE_PEDIDO, asi el
# filtro del admin no puede ofrecer un estado que el ciclo de vida no conozca.
ETIQUETAS_DE_ESTADO: dict[str, str] = {
    "en espera": "En espera",
    "enviado": "Enviado",
    "entregado": "Entregado",
    "cancelado": "Cancelado",
}


@dataclass(frozen=True)
class PedidoEnLista:
    """One row of the admin order list, ready to render."""

    id: int
    fecha: str
    cliente: str
    email: str
    estado: str
    estado_etiqueta: str
    total: str
    unidades: int


@dataclass(frozen=True)
class PaginaDePedidos:
    pedidos: list[PedidoEnLista]
    total: int
    pagina: int
    total_paginas: int
    filtro_estado: str
    busqueda: str

    @property
    def hay_anterior(self) -> bool:
        return self.pagina > 1

    @property
    def hay_siguiente(self) -> bool:
        return self.pagina < self.total_paginas


@dataclass(frozen=True)
class LineaDePedido:
    """Snapshot line plus the product name, which the snapshot does not store."""

    producto: str
    color: str
    talle: str
    cantidad: int
    precio_unitario: str
    subtotal: str


@dataclass(frozen=True)
class DetalleDePedido:
    id: int
    fecha: str
    cliente: str
    email: str
    estado: str
    estado_etiqueta: str
    total: str
    unidades: int
    envio: str
    lineas: list[LineaDePedido]


def etiqueta_de_estado(estado: str) -> str:
    """Human label for a state; unknown values fall back to the raw text."""
    return ETIQUETAS_DE_ESTADO.get(estado, estado)


def opciones_de_estado() -> list[dict[str, str]]:
    """Options for the admin filter, in lifecycle order (T-044, D-030)."""
    return [
        {"valor": estado, "texto": etiqueta_de_estado(estado)}
        for estado in ESTADOS_DE_PEDIDO
    ]


def normalizar_filtro(estado: str | None) -> str:
    """Ignore an unknown state instead of failing on a stale link."""
    return estado if estado in ESTADOS_DE_PEDIDO else ""


def estados_siguientes(estado: str) -> list[dict[str, str]]:
    """Allowed transitions from ``estado`` with their labels (T-044).

    The detail page paints one button per entry; it never invents a transition.
    """
    return [
        {"valor": siguiente, "texto": etiqueta_de_estado(siguiente)}
        for siguiente in TRANSICIONES.get(estado, ())
    ]


def _fecha(momento: datetime) -> str:
    return momento.strftime("%d/%m/%Y %H:%M")


def _cliente(perfil: UserProfile | None, usuario_id: int) -> tuple[str, str]:
    """Return (display name, email) for the order row."""
    if perfil is None:
        return f"Usuario #{usuario_id}", ""
    nombre = f"{perfil.nombre} {perfil.apellido}".strip()
    return nombre or perfil.email, perfil.email


def _a_pedido_en_lista(
    pedido,
    perfil: UserProfile | None,
    unidades: int,
) -> PedidoEnLista:
    cliente, email = _cliente(perfil, pedido.usuario_id)
    return PedidoEnLista(
        id=pedido.id_pedido or 0,
        fecha=_fecha(pedido.fecha_pedido),
        cliente=cliente,
        email=email,
        estado=pedido.estado,
        estado_etiqueta=etiqueta_de_estado(pedido.estado),
        total=formatear_precio(pedido.total),
        unidades=int(unidades or 0),
    )


def listar_pedidos(
    *,
    estado: str = "",
    busqueda: str = "",
    pagina: int = 1,
) -> PaginaDePedidos:
    """One page of orders for the admin panel (D-030).

    The filters are applied in the query, not in the page: the pagination count
    has to see the same rows the table shows.
    """
    filtro = normalizar_filtro(estado)
    busqueda_limpia = (busqueda or "").strip()
    total = pedido_repositorio.contar_pedidos(
        estado=filtro,
        busqueda=busqueda_limpia,
    )
    total_paginas = max(1, math.ceil(total / PEDIDOS_POR_PAGINA))
    actual = min(max(1, int(pagina or 1)), total_paginas)

    filas = pedido_repositorio.listar_pedidos(
        estado=filtro,
        busqueda=busqueda_limpia,
        offset=(actual - 1) * PEDIDOS_POR_PAGINA,
        limite=PEDIDOS_POR_PAGINA,
    )

    return PaginaDePedidos(
        pedidos=[_a_pedido_en_lista(*fila) for fila in filas],
        total=total,
        pagina=actual,
        total_paginas=total_paginas,
        filtro_estado=filtro,
        busqueda=busqueda_limpia,
    )


def obtener_detalle(pedido_id: int) -> DetalleDePedido:
    """Order detail with its snapshot lines, address and totals (D-029, D-030)."""
    fila = pedido_repositorio.obtener_pedido(pedido_id)
    if fila is None:
        raise ErrorDePedido(f"No existe el pedido #{pedido_id}.")

    pedido, perfil = fila
    cliente, email = _cliente(perfil, pedido.usuario_id)

    lineas = [
        LineaDePedido(
            producto=producto.nombre if producto else "Producto eliminado",
            color=item.color,
            talle=item.talle,
            cantidad=item.cantidad,
            precio_unitario=formatear_precio(item.precio_unitario),
            subtotal=formatear_precio(item.precio_unitario * item.cantidad),
        )
        for item, producto in pedido_repositorio.listar_lineas(pedido_id)
    ]

    partes_del_envio = [
        f"{pedido.direccion} {pedido.numero}".strip(),
        pedido.departamento,
        pedido.ciudad,
        pedido.provincia,
        f"CP {pedido.codigo_postal}" if pedido.codigo_postal else "",
    ]

    return DetalleDePedido(
        id=pedido.id_pedido or 0,
        fecha=_fecha(pedido.fecha_pedido),
        cliente=cliente,
        email=email,
        estado=pedido.estado,
        estado_etiqueta=etiqueta_de_estado(pedido.estado),
        total=formatear_precio(pedido.total),
        unidades=sum(linea.cantidad for linea in lineas),
        envio=", ".join(parte for parte in partes_del_envio if parte),
        lineas=lineas,
    )

