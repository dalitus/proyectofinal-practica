"""Order persistence: creation and state changes (T-043, T-044, D-004, D-010).

One transaction does the whole purchase: lock the variants, revalidate the stock,
discount it, write the order with its snapshot lines and empty the cart. If any
step fails, nothing is written and the stock stays where it was (D-004).

``FOR UPDATE`` on the ``stocks`` rows is what stops two buyers from taking the
last unit at the same time: the second transaction waits and then sees the new
quantity instead of a stale read.

A state change locks the order row and rechecks the state the caller read, so a
double click or two admins cannot apply the same transition twice. Cancelling
also adds the order lines back to their variants (D-010).

SQL only: no HTTP, no UI, no messages, no state machine. The service owns the
valid transitions and builds the texts.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import delete, func, or_
from sqlmodel import Session, select

from app.model.carrito_model import Carrito
from app.model.pedido_item_modelo import PedidoItem
from app.model.pedido_model import Pedido
from app.model.perfil_modelo import UserProfile
from app.model.product_model import Producto
from app.model.stock_model import Stocks
from app.repository.conect_db import get_session


class StockInsuficiente(Exception):
    """The variant ran out between the cart and the checkout (D-004).

    Neutral on purpose: the repository does not write user-facing copy, the
    service turns this into a message with the product name.
    """

    def __init__(
        self,
        *,
        nombre: str,
        color: str,
        talle: str,
        disponible: int,
    ) -> None:
        super().__init__(nombre)
        self.nombre = nombre
        self.color = color
        self.talle = talle
        self.disponible = disponible


class PedidoNoEncontrado(Exception):
    """The order id does not exist (maybe it was never created)."""

    def __init__(self, pedido_id: int) -> None:
        super().__init__(pedido_id)
        self.pedido_id = pedido_id


class EstadoCambiado(Exception):
    """The order is no longer in the state the caller read.

    Another admin (or a double click) got there first. The caller must not
    overwrite that change; it reloads and decides again.
    """

    def __init__(self, *, estado_actual: str, estado_esperado: str) -> None:
        super().__init__(estado_actual)
        self.estado_actual = estado_actual
        self.estado_esperado = estado_esperado


def crear_pedido(
    *,
    usuario_id: int,
    lineas: list[dict[str, object]],
    entrega: dict[str, str],
    total: Decimal,
) -> int:
    """Create the order, discount the stock and empty the cart atomically.

    ``lineas`` items carry ``variante_id``, ``cantidad``, ``color``, ``talle`` and
    ``precio_unitario``: the colour, the size and the price are snapshotted, so a
    later price change does not rewrite history (D-029).
    """
    if not lineas:
        raise StockInsuficiente(nombre="", color="", talle="", disponible=0)

    variantes_ids = sorted({int(linea["variante_id"]) for linea in lineas})  # type: ignore[arg-type]

    with get_session() as session:
        variantes = {
            variante.id_stock: variante
            for variante in session.exec(
                select(Stocks)
                .where(Stocks.id_stock.in_(variantes_ids))
                .with_for_update()
            ).all()
        }

        productos = {
            producto.id: producto
            for producto in session.exec(
                select(Producto).where(
                    Producto.id.in_(
                        {variante.producto_id for variante in variantes.values()}
                    )
                )
            ).all()
        }

        for linea in lineas:
            variante = variantes.get(int(linea["variante_id"]))  # type: ignore[arg-type]
            if variante is None:
                raise StockInsuficiente(
                    nombre="",
                    color=str(linea["color"]),
                    talle=str(linea["talle"]),
                    disponible=0,
                )

            producto = productos.get(variante.producto_id)
            cantidad = int(linea["cantidad"])  # type: ignore[arg-type]
            disponible = int(variante.cantidad_disponible)

            if producto is None or not producto.activo or disponible < cantidad:
                raise StockInsuficiente(
                    nombre=producto.nombre if producto else "",
                    color=variante.color,
                    talle=variante.talle,
                    disponible=disponible,
                )

            variante.cantidad_disponible = disponible - cantidad
            session.add(variante)

        pedido = Pedido(
            usuario_id=usuario_id,
            total=total,
            direccion=entrega.get("direccion", ""),
            numero=entrega.get("numero", ""),
            departamento=entrega.get("departamento", ""),
            codigo_postal=entrega.get("codigo_postal", ""),
            ciudad=entrega.get("ciudad", ""),
            provincia=entrega.get("provincia", ""),
        )
        session.add(pedido)
        session.flush()

        for linea in lineas:
            session.add(
                PedidoItem(
                    pedido_id=pedido.id_pedido or 0,
                    variante_id=int(linea["variante_id"]),  # type: ignore[arg-type]
                    color=str(linea["color"]),
                    talle=str(linea["talle"]),
                    cantidad=int(linea["cantidad"]),  # type: ignore[arg-type]
                    precio_unitario=linea["precio_unitario"],  # type: ignore[arg-type]
                )
            )

        # El carrito se vacia en la misma transaccion: si algo falla, sigue lleno.
        session.execute(delete(Carrito).where(Carrito.usuario_id == usuario_id))
        session.commit()

        return pedido.id_pedido or 0


def obtener_estado(pedido_id: int) -> str:
    """Return the state stored for the order.

    Raises ``PedidoNoEncontrado`` instead of returning ``None``: the service
    needs to tell "no such order" apart from "empty state".
    """
    with get_session() as session:
        estado = session.exec(
            select(Pedido.estado).where(Pedido.id_pedido == pedido_id)
        ).first()
        if estado is None:
            raise PedidoNoEncontrado(pedido_id)
        return estado


def _reponer_stock(session: Session, pedido_id: int) -> None:
    """Add the order lines back to their variants (D-010).

    The lines are summed in Python and the variants are locked in id order, the
    same lock order ``crear_pedido`` uses: two transactions touching the same
    variants cannot deadlock by taking the rows in opposite order.
    """
    items = session.exec(
        select(PedidoItem).where(PedidoItem.pedido_id == pedido_id)
    ).all()

    por_variante: dict[int, int] = {}
    for item in items:
        por_variante[item.variante_id] = (
            por_variante.get(item.variante_id, 0) + item.cantidad
        )

    if not por_variante:
        return

    variantes = {
        variante.id_stock: variante
        for variante in session.exec(
            select(Stocks)
            .where(Stocks.id_stock.in_(sorted(por_variante)))
            .order_by(Stocks.id_stock)
            .with_for_update()
        ).all()
    }

    for variante_id in sorted(por_variante):
        variante = variantes.get(variante_id)
        if variante is None:
            # The variant was deleted with the product: nothing to restore.
            continue
        variante.cantidad_disponible += por_variante[variante_id]
        session.add(variante)


def cambiar_estado(
    *,
    pedido_id: int,
    estado_esperado: str,
    estado_nuevo: str,
    fecha_entrega: datetime | None = None,
    fecha_cancelacion: datetime | None = None,
    reponer_stock: bool = False,
) -> None:
    """Write the new state in one transaction, guarding against races.

    The service passes the state it validated. If the row moved in the meantime
    ``EstadoCambiado`` is raised and nothing is written. ``reponer_stock`` is the
    service's decision (cancellation, D-010), not a rule of this layer.
    """
    with get_session() as session:
        pedido = session.exec(
            select(Pedido)
            .where(Pedido.id_pedido == pedido_id)
            .with_for_update()
        ).first()

        if pedido is None:
            raise PedidoNoEncontrado(pedido_id)

        if pedido.estado != estado_esperado:
            raise EstadoCambiado(
                estado_actual=pedido.estado,
                estado_esperado=estado_esperado,
            )

        if reponer_stock:
            _reponer_stock(session, pedido_id)

        pedido.estado = estado_nuevo
        if fecha_entrega is not None:
            pedido.fecha_entrega = fecha_entrega
        if fecha_cancelacion is not None:
            pedido.fecha_cancelacion = fecha_cancelacion

        session.add(pedido)
        session.commit()


# --------------------------------------------------------------------------
# Listado y detalle para el panel del admin (T-051, D-030)
# --------------------------------------------------------------------------

# Unidades compradas por pedido, como subconsulta: el listado necesita el dato
# sin disparar una consulta por fila.
_UNIDADES = (
    select(func.coalesce(func.sum(PedidoItem.cantidad), 0))
    .where(PedidoItem.pedido_id == Pedido.id_pedido)
    .correlate(Pedido)
    .scalar_subquery()
)


def _condiciones_de_pedidos(*, estado: str, busqueda: str) -> list:
    """Build the WHERE clauses shared by the page query and the count."""
    condiciones: list = []

    if estado:
        condiciones.append(Pedido.estado == estado)

    termino = (busqueda or "").strip()
    if termino:
        patron = f"%{termino}%"
        coincidencias = [
            UserProfile.nombre.ilike(patron),
            UserProfile.apellido.ilike(patron),
            UserProfile.email.ilike(patron),
            # El admin tambien busca por producto: linea -> variante -> producto.
            select(PedidoItem.id)
            .join(Stocks, Stocks.id_stock == PedidoItem.variante_id)
            .join(Producto, Producto.id == Stocks.producto_id)
            .where(
                PedidoItem.pedido_id == Pedido.id_pedido,
                Producto.nombre.ilike(patron),
            )
            .correlate(Pedido)
            .exists(),
        ]
        if termino.isdigit():
            coincidencias.append(Pedido.id_pedido == int(termino))
        condiciones.append(or_(*coincidencias))

    return condiciones


def listar_pedidos(
    *,
    estado: str = "",
    busqueda: str = "",
    offset: int = 0,
    limite: int = 10,
) -> list[tuple[Pedido, UserProfile | None, int]]:
    """One page of orders, newest first, with the buyer profile and unit count."""
    condiciones = _condiciones_de_pedidos(estado=estado, busqueda=busqueda)

    with get_session() as session:
        consulta = (
            select(Pedido, UserProfile, _UNIDADES)
            .join(
                UserProfile,
                UserProfile.local_user_id == Pedido.usuario_id,
                isouter=True,
            )
            .where(*condiciones)
            .order_by(Pedido.fecha_pedido.desc(), Pedido.id_pedido.desc())
            .offset(offset)
            .limit(limite)
        )
        return [tuple(fila) for fila in session.exec(consulta).all()]  # type: ignore[misc]


def contar_pedidos(*, estado: str = "", busqueda: str = "") -> int:
    """Total of orders matching the same filters as the page query."""
    condiciones = _condiciones_de_pedidos(estado=estado, busqueda=busqueda)

    with get_session() as session:
        return session.exec(
            select(func.count())
            .select_from(Pedido)
            .join(
                UserProfile,
                UserProfile.local_user_id == Pedido.usuario_id,
                isouter=True,
            )
            .where(*condiciones)
        ).one()


def obtener_pedido(pedido_id: int) -> tuple[Pedido, UserProfile | None] | None:
    """One order with its buyer profile, or ``None``."""
    with get_session() as session:
        consulta = (
            select(Pedido, UserProfile)
            .join(
                UserProfile,
                UserProfile.local_user_id == Pedido.usuario_id,
                isouter=True,
            )
            .where(Pedido.id_pedido == pedido_id)
        )
        fila = session.exec(consulta).first()
        return tuple(fila) if fila else None  # type: ignore[misc]


def listar_lineas(pedido_id: int) -> list[tuple[PedidoItem, Producto | None]]:
    """Order lines with the current product name, in insertion order.

    The price and the size come from the snapshot in ``PedidoItem`` (D-029); the
    product name is read live because the snapshot does not store it.
    """
    with get_session() as session:
        consulta = (
            select(PedidoItem, Producto)
            .join(
                Stocks,
                Stocks.id_stock == PedidoItem.variante_id,
                isouter=True,
            )
            .join(Producto, Producto.id == Stocks.producto_id, isouter=True)
            .where(PedidoItem.pedido_id == pedido_id)
            .order_by(PedidoItem.id)
        )
        return [tuple(fila) for fila in session.exec(consulta).all()]  # type: ignore[misc]
