from sqlmodel import select, or_
from sqlalchemy.orm import selectinload
from proyectofinal.model.product_model import Producto
from proyectofinal.repository.conect_db import get_session

def get_all_productos() -> list[Producto]:
    with get_session() as session:
        # Eager-load stock relationship to avoid DetachedInstanceError when accessing after session closes
        query = select(Producto).options(selectinload(Producto.stock))
        return session.exec(query).all()

def buscar_productos_por_texto(texto: str) -> list[Producto]:
    with get_session() as session:
        query = select(Producto).where(
            or_(
                Producto.nombre.ilike(f"%{texto}%"),
                Producto.marca.ilike(f"%{texto}%")
            )
        ).options(selectinload(Producto.stock))
        return session.exec(query).all()