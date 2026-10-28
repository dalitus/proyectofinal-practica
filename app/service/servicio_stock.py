# app/service/stock_servicio.py

from sqlmodel import Session, select
from app.model.stock_model import Stocks
from app.repository.conect_db import engine

# Crear un registro de stock (color + cantidad)
def crear_stock(producto_id: int, color: str, cantidad_disponible: int) -> Stocks:
    with Session(engine) as session:
        nuevo = Stocks(
            producto_id=producto_id,   # 👈 coincide con la FK en Stocks
            color=color,
            cantidad_disponible=cantidad_disponible
        )
        session.add(nuevo)
        session.commit()
        session.refresh(nuevo)
        return nuevo

# Obtener todos los stocks de un producto
def obtener_stocks_por_producto(producto_id: int) -> list[Stocks]:
    with Session(engine) as session:
        statement = select(Stocks).where(Stocks.producto_id == producto_id)
        results = session.exec(statement).all()
        return results

# Editar un stock existente
def editar_stock(id_stock: int, data: dict) -> Stocks | None:
    with Session(engine) as session:
        stock = session.get(Stocks, id_stock)
        if not stock:
            return None
        for key, value in data.items():
            setattr(stock, key, value)
        session.add(stock)
        session.commit()
        session.refresh(stock)
        return stock

# Eliminar un stock
def eliminar_stock(id_stock: int) -> bool:
    with Session(engine) as session:
        stock = session.get(Stocks, id_stock)
        if not stock:
            return False
        session.delete(stock)
        session.commit()
        return True

# Obtener un stock por ID
def obtener_stock_por_id(id_stock: int) -> Stocks | None:
    with Session(engine) as session:
        return session.get(Stocks, id_stock)

# Listar todos los stocks (opcional, útil para administración)
def obtener_todos_los_stocks() -> list[Stocks]:
    with Session(engine) as session:
        statement = select(Stocks)
        return session.exec(statement).all()