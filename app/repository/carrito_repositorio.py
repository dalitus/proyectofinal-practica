"""Cart queries (T-040).

SQL only: no HTTP, no UI, no formatting. Every function opens and closes its own
session (D-033) so the state layer never touches the engine (T-062).

A cart line points at a variant, not at a product (D-009): ``carritos.variante_id``
is a ``stocks`` id, so "negro 40" and "negro 41" are two different lines.
"""

from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.model.carrito_modelo import Carrito
from app.model.producto_modelo import Producto
from app.model.variante_modelo import Stocks
from app.repository.base_de_datos import get_session


def listar_lineas(usuario_id: int) -> list[tuple[Carrito, Stocks, Producto]]:
    """Every line of the user's cart with its variant and product.

    One join instead of a query per line: the cart page needs the name, the price
    and the stock of each variant on every render.
    """
    with get_session() as session:
        consulta = (
            select(Carrito, Stocks, Producto)
            .join(Stocks, Carrito.variante_id == Stocks.id_stock)
            .join(Producto, Stocks.producto_id == Producto.id)
            .where(Carrito.usuario_id == usuario_id)
            .order_by(Carrito.id_carrito)
        )
        return [tuple(fila) for fila in session.exec(consulta).all()]  # type: ignore[misc]


def contar_unidades(usuario_id: int) -> int:
    """Total units in the user's cart, in one SUM (T-078).

    The header badge needs a number, not the whole cart: summing in SQL keeps
    every page load at one cheap query instead of a join and a Python loop.
    """
    with get_session() as session:
        total = session.exec(
            select(func.coalesce(func.sum(Carrito.cantidad), 0)).where(
                Carrito.usuario_id == usuario_id
            )
        ).one()

    return int(total)


def obtener_variante(variante_id: int) -> tuple[Stocks, Producto] | None:
    """The variant with its own stock and the product it belongs to."""
    with get_session() as session:
        consulta = (
            select(Stocks, Producto)
            .join(Producto, Stocks.producto_id == Producto.id)
            .where(Stocks.id_stock == variante_id)
        )
        fila = session.exec(consulta).first()

    return (fila[0], fila[1]) if fila else None


def obtener_linea(usuario_id: int, variante_id: int) -> Carrito | None:
    """The line for that variant, if the user already added it."""
    with get_session() as session:
        return session.exec(
            select(Carrito).where(
                Carrito.usuario_id == usuario_id,
                Carrito.variante_id == variante_id,
            )
        ).one_or_none()


def obtener_linea_por_id(usuario_id: int, linea_id: int) -> Carrito | None:
    """One line, scoped to its owner so an id from another cart goes nowhere."""
    with get_session() as session:
        return session.exec(
            select(Carrito).where(
                Carrito.id_carrito == linea_id,
                Carrito.usuario_id == usuario_id,
            )
        ).one_or_none()


def crear_linea(*, usuario_id: int, variante_id: int, cantidad: int) -> None:
    """Insert a line; a concurrent insert of the same variant adds up instead of failing.

    ``uq_carrito_usuario_variante`` is the real guard: two tabs adding the same
    variant at once cannot create two lines. The service validated the stock just
    before and the checkout revalidates (D-004).
    """
    with get_session() as session:
        session.add(
            Carrito(
                usuario_id=usuario_id,
                variante_id=variante_id,
                cantidad=cantidad,
            )
        )
        try:
            session.commit()
            return
        except IntegrityError:
            session.rollback()

        linea = session.exec(
            select(Carrito).where(
                Carrito.usuario_id == usuario_id,
                Carrito.variante_id == variante_id,
            )
        ).one_or_none()
        if linea is None:  # la otra transaccion borro la linea: se reintenta una vez
            session.add(
                Carrito(
                    usuario_id=usuario_id,
                    variante_id=variante_id,
                    cantidad=cantidad,
                )
            )
        else:
            linea.cantidad = linea.cantidad + cantidad
            session.add(linea)
        session.commit()


def actualizar_cantidad(*, linea_id: int, cantidad: int) -> None:
    """Set the quantity of an existing line."""
    with get_session() as session:
        linea = session.exec(select(Carrito).where(Carrito.id_carrito == linea_id)).one_or_none()
        if linea is None:
            return
        linea.cantidad = cantidad
        session.add(linea)
        session.commit()


def borrar_linea(linea_id: int) -> None:
    """Delete one line; deleting an already gone line is not an error."""
    with get_session() as session:
        linea = session.exec(select(Carrito).where(Carrito.id_carrito == linea_id)).one_or_none()
        if linea is None:
            return
        session.delete(linea)
        session.commit()


def vaciar(usuario_id: int) -> None:
    """Delete every line of the user's cart."""
    with get_session() as session:
        for linea in session.exec(select(Carrito).where(Carrito.usuario_id == usuario_id)).all():
            session.delete(linea)
        session.commit()
