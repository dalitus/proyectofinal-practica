"""Catalog queries (T-030, T-033).

SQL only: no HTTP, no UI, no formatting. Every function opens and closes its own
session (D-033) so the state layer never touches the engine (T-062).

Filters are built as one list of conditions shared by the page query and the
count query, so the two can never disagree about what "matches".
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.model.categoria_modelo import Categoria
from app.model.product_model import Producto
from app.model.stock_model import Stocks
from app.repository.conect_db import get_session

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
