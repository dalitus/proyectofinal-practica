"""Catalog and admin queries (T-030, T-033, T-050).

SQL only: no HTTP, no UI, no formatting. Every function opens and closes its own
session (D-033) so the state layer never touches the engine (T-062).

Filters are built as one list of conditions shared by the page query and the
count query, so the two can never disagree about what "matches".

The admin functions live at the bottom: they also see inactive products (D-028)
and write in one transaction per operation, so a product never ends up without
its variants (D-049).
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import delete, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.model.carrito_modelo import Carrito
from app.model.categoria_modelo import Categoria
from app.model.pedido_item_modelo import PedidoItem
from app.model.producto_modelo import Producto
from app.model.variante_modelo import Stocks
from app.repository.base_de_datos import get_session

# Sort key -> ORDER BY clauses. The name tiebreaker keeps pages stable.
_ORDENAMIENTOS = {
    "nombre": (Producto.nombre.asc(), Producto.id.asc()),
    "precio_asc": (Producto.precio.asc(), Producto.nombre.asc()),
    "precio_desc": (Producto.precio.desc(), Producto.nombre.asc()),
}


def _existe_variante(campo: Any, valor: str) -> Any:
    """Require at least one variant with that size or colour (D-014).

    An ``EXISTS`` subquery instead of a join: a product with three sizes must
    count once, not three times.
    """
    return (
        select(Stocks.id_stock)
        .where(Stocks.producto_id == Producto.id, campo == valor)
        .correlate(Producto)
        .exists()
    )


def _condiciones(
    *,
    busqueda: str = "",
    categoria_id: int | None = None,
    talle: str | None = None,
    color: str | None = None,
) -> list[Any]:
    """Return the WHERE clauses for the catalog filters (D-014)."""
    condiciones: list[Any] = [Producto.activo.is_(True)]

    texto = (busqueda or "").strip()
    if texto:
        patron = f"%{texto}%"
        condiciones.append(
            Producto.nombre.ilike(patron) | Producto.marca.ilike(patron)
        )
    if categoria_id is not None:
        condiciones.append(Producto.categoria_id == categoria_id)
    if talle:
        condiciones.append(_existe_variante(Stocks.talle, talle))
    if color:
        condiciones.append(_existe_variante(Stocks.color, color))

    return condiciones


def listar_productos(
    *,
    busqueda: str = "",
    categoria_id: int | None = None,
    talle: str | None = None,
    color: str | None = None,
    orden: str = "nombre",
    limite: int = 12,
    offset: int = 0,
) -> list[Producto]:
    """Return one page of active products with their variants and category."""
    condiciones = _condiciones(
        busqueda=busqueda,
        categoria_id=categoria_id,
        talle=talle,
        color=color,
    )
    ordenamiento = _ORDENAMIENTOS.get(orden, _ORDENAMIENTOS["nombre"])

    with get_session() as session:
        consulta = (
            select(Producto)
            .where(*condiciones)
            .options(
                selectinload(Producto.stocks),
                selectinload(Producto.categoria),
            )
            .order_by(*ordenamiento)
            .offset(offset)
            .limit(limite)
        )
        return list(session.exec(consulta).all())


def contar_productos(
    *,
    busqueda: str = "",
    categoria_id: int | None = None,
    talle: str | None = None,
    color: str | None = None,
) -> int:
    """Total of active products matching the same filters as the page query."""
    condiciones = _condiciones(
        busqueda=busqueda,
        categoria_id=categoria_id,
        talle=talle,
        color=color,
    )

    with get_session() as session:
        return session.exec(
            select(func.count()).select_from(Producto).where(*condiciones)
        ).one()


def obtener_producto(producto_id: int) -> Producto | None:
    """One active product with its variants and category, or ``None``.

    Inactive products answer ``None`` as well: a soft-deleted product (D-028)
    must not be reachable by guessing its id.
    """
    with get_session() as session:
        consulta = (
            select(Producto)
            .where(Producto.id == producto_id, Producto.activo.is_(True))
            .options(
                selectinload(Producto.stocks),
                selectinload(Producto.categoria),
            )
        )
        return session.exec(consulta).first()


def listar_categorias() -> list[Categoria]:
    """Categories with at least one active product, ordered by name."""
    with get_session() as session:
        consulta = (
            select(Categoria)
            .where(
                select(Producto.id)
                .where(
                    Producto.categoria_id == Categoria.id,
                    Producto.activo.is_(True),
                )
                .correlate(Categoria)
                .exists()
            )
            .order_by(Categoria.nombre)
        )
        return list(session.exec(consulta).all())


def listar_talles() -> list[str]:
    """Distinct sizes across all variants, ordered by label.

    Sizes are numeric labels ("38".."43"), so the label order is the natural
    one; a non-numeric scale would need its own sort key.
    """
    with get_session() as session:
        return list(
            session.exec(select(Stocks.talle).distinct().order_by(Stocks.talle)).all()
        )


def listar_colores() -> list[str]:
    """Distinct colours across all variants, ordered by label."""
    with get_session() as session:
        return list(
            session.exec(select(Stocks.color).distinct().order_by(Stocks.color)).all()
        )


# --------------------------------------------------------------------------
# Panel del admin (T-050, D-028, D-049)
# --------------------------------------------------------------------------


class ProductoNoEncontrado(Exception):
    """The product id does not exist, not even as an inactive row."""

    def __init__(self, producto_id: int) -> None:
        super().__init__(producto_id)
        self.producto_id = producto_id


class VarianteNoEncontrada(Exception):
    """The variant id does not exist or belongs to another product."""

    def __init__(self, variante_id: int) -> None:
        super().__init__(variante_id)
        self.variante_id = variante_id


class VarianteDuplicada(Exception):
    """The same ``(producto, color, talle)`` already exists (D-009).

    The unique index is the last line of defence: the service checks first for a
    friendly message, but two admins can still race. Translating the
    ``IntegrityError`` here keeps the transaction rolled back and the message in
    the service layer.
    """


class VarianteEnUso(Exception):
    """The variant is referenced by a cart line or an order line.

    Deleting it would break the history (D-029), so the service explains the
    alternative: leave it with zero stock.
    """


def _condiciones_admin(*, busqueda: str = "", estado: str = "activos") -> list[Any]:
    """WHERE clauses for the admin list; "todos" adds no state filter."""
    condiciones: list[Any] = []

    texto = (busqueda or "").strip()
    if texto:
        patron = f"%{texto}%"
        condiciones.append(Producto.nombre.ilike(patron) | Producto.marca.ilike(patron))
    if estado == "activos":
        condiciones.append(Producto.activo.is_(True))
    elif estado == "inactivos":
        condiciones.append(Producto.activo.is_(False))

    return condiciones


def listar_para_admin(
    *,
    busqueda: str = "",
    estado: str = "activos",
    limite: int = 10,
    offset: int = 0,
) -> list[Producto]:
    """One page of products for the panel, inactive included when asked."""
    with get_session() as session:
        consulta = (
            select(Producto)
            .where(*_condiciones_admin(busqueda=busqueda, estado=estado))
            .options(
                selectinload(Producto.stocks),
                selectinload(Producto.categoria),
            )
            .order_by(Producto.nombre.asc(), Producto.id.asc())
            .offset(offset)
            .limit(limite)
        )
        return list(session.exec(consulta).all())


def contar_para_admin(*, busqueda: str = "", estado: str = "activos") -> int:
    """Total of products matching the admin filters."""
    with get_session() as session:
        return session.exec(
            select(func.count())
            .select_from(Producto)
            .where(*_condiciones_admin(busqueda=busqueda, estado=estado))
        ).one()


def listar_todas_las_categorias() -> list[Categoria]:
    """Every category, even the ones with no products: the form needs them."""
    with get_session() as session:
        return list(session.exec(select(Categoria).order_by(Categoria.nombre)).all())


def obtener_para_editar(producto_id: int) -> Producto | None:
    """One product with its variants, active or not (the panel edits both)."""
    with get_session() as session:
        consulta = (
            select(Producto)
            .where(Producto.id == producto_id)
            .options(
                selectinload(Producto.stocks),
                selectinload(Producto.categoria),
            )
        )
        return session.exec(consulta).first()


def crear_producto(
    datos: dict[str, Any],
    variantes: list[dict[str, Any]],
) -> int:
    """Create the product and its variants in one transaction (D-049).

    Either everything is written or nothing is: a variant that repeats
    ``(color, talle)`` rolls the whole product back.
    """
    with get_session() as session:
        producto = Producto(**datos)
        session.add(producto)
        try:
            session.flush()
            for variante in variantes:
                session.add(
                    Stocks(
                        producto_id=producto.id or 0,
                        color=variante["color"],
                        talle=variante["talle"],
                        cantidad_disponible=variante["cantidad"],
                    )
                )
            session.commit()
        except IntegrityError as error:
            session.rollback()
            raise VarianteDuplicada(str(error.orig)) from error

        return producto.id or 0


def actualizar_producto(producto_id: int, datos: dict[str, Any]) -> None:
    """Write the product fields; the variants are edited one by one."""
    with get_session() as session:
        producto = session.get(Producto, producto_id)
        if producto is None:
            raise ProductoNoEncontrado(producto_id)

        for campo, valor in datos.items():
            setattr(producto, campo, valor)
        session.add(producto)
        session.commit()


def cambiar_activo(producto_id: int, *, activo: bool) -> None:
    """Soft delete or reactivate a product (D-028); the variants stay."""
    with get_session() as session:
        producto = session.get(Producto, producto_id)
        if producto is None:
            raise ProductoNoEncontrado(producto_id)

        producto.activo = activo
        session.add(producto)
        session.commit()


def variante_por_combinacion(
    producto_id: int,
    color: str,
    talle: str,
    *,
    excluir_id: int | None = None,
) -> int | None:
    """Id of the variant with that colour and size, if any (D-009)."""
    with get_session() as session:
        consulta = select(Stocks.id_stock).where(
            Stocks.producto_id == producto_id,
            Stocks.color == color,
            Stocks.talle == talle,
        )
        if excluir_id is not None:
            consulta = consulta.where(Stocks.id_stock != excluir_id)

        return session.exec(consulta).first()


def _referencias(session: Any, variante_id: int) -> bool:
    """True when a cart line or an order line points at the variant."""
    en_carrito = session.exec(
        select(Carrito.id_carrito).where(Carrito.variante_id == variante_id)
    ).first()
    if en_carrito is not None:
        return True
    return (
        session.exec(
            select(PedidoItem.id).where(PedidoItem.variante_id == variante_id)
        ).first()
        is not None
    )


def variante_en_uso(variante_id: int) -> bool:
    """True when a cart line or an order line points at the variant."""
    with get_session() as session:
        return _referencias(session, variante_id)


def agregar_variante(
    producto_id: int,
    *,
    color: str,
    talle: str,
    cantidad: int,
) -> int:
    """Add one variant to an existing product."""
    with get_session() as session:
        if session.get(Producto, producto_id) is None:
            raise ProductoNoEncontrado(producto_id)

        variante = Stocks(
            producto_id=producto_id,
            color=color,
            talle=talle,
            cantidad_disponible=cantidad,
        )
        session.add(variante)
        try:
            session.commit()
        except IntegrityError as error:
            session.rollback()
            raise VarianteDuplicada(str(error.orig)) from error

        return variante.id_stock or 0


def actualizar_variante(
    producto_id: int,
    variante_id: int,
    *,
    color: str,
    talle: str,
    cantidad: int,
) -> None:
    """Edit one variant of that product; an unknown id is an error, not a no-op."""
    with get_session() as session:
        variante = session.get(Stocks, variante_id)
        if variante is None or variante.producto_id != producto_id:
            raise VarianteNoEncontrada(variante_id)

        variante.color = color
        variante.talle = talle
        variante.cantidad_disponible = cantidad
        session.add(variante)
        try:
            session.commit()
        except IntegrityError as error:
            session.rollback()
            raise VarianteDuplicada(str(error.orig)) from error


def eliminar_variante(producto_id: int, variante_id: int) -> None:
    """Delete a variant that nothing references.

    A variant that was ever sold keeps its row: the order snapshot already has
    colour and size, but the foreign key still points here (D-029).
    """
    with get_session() as session:
        variante = session.get(Stocks, variante_id)
        if variante is None or variante.producto_id != producto_id:
            raise VarianteNoEncontrada(variante_id)

        if _referencias(session, variante_id):
            raise VarianteEnUso(variante_id)

        session.execute(delete(Stocks).where(Stocks.id_stock == variante_id))
        session.commit()
