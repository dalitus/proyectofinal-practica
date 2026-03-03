from sqlmodel import Session, select
from proyectofinal.model.carrito_model import Carrito
from proyectofinal.model.product_model import Producto
from proyectofinal.model import Users
from proyectofinal.repository.conect_db import engine

# 🔍 Obtener carrito agrupado por producto
def obtener_carrito_agrupado_por_usuario(db: Session, id_users: int) -> list[dict]:
    resultados = obtener_carrito_completo_por_usuario(db, id_users)
    agrupados = []
    for carrito, producto, usuario in resultados:
        agrupados.append({
            "id_producto": producto.id_producto,
            "nombre": producto.nombre,
            "precio": float(producto.precio),
            "imagen": producto.imagen,
            "cantidad": carrito.cantidad,
            "subtotal": float(producto.precio) * carrito.cantidad
        })
    return agrupados

# 🔍 Obtener carrito completo con joins
def obtener_carrito_completo_por_usuario(db: Session, id_users: int):
    return (
        db.query(Carrito, Producto, Users)
        .join(Producto, Carrito.id_producto == Producto.id_producto)
        .join(Users, Carrito.id_users == Users.id_users)
        .filter(Carrito.id_users == id_users)
        .all()
    )

# 🔍 Obtener items sin joins (solo IDs)
def get_items_por_usuario(user_id: int) -> list[dict]:
    with Session(engine) as session:
        resultados = session.exec(
            select(Carrito).where(Carrito.id_users == user_id)
        ).all()
        return [r.dict() for r in resultados]

# ✅ Agregar producto al carrito
def agregar_item_al_carrito(id_users: int, id_producto: int) -> None:
    if id_users is None:
        raise ValueError("id_users no puede ser None al agregar al carrito.")
    with Session(engine) as session:
        item = session.exec(
            select(Carrito).where(
                Carrito.id_users == id_users,
                Carrito.id_producto == id_producto
            )
        ).first()
        if item:
            item.cantidad += 1
            session.add(item)
        else:
            item = Carrito(id_users=id_users, id_producto=id_producto, cantidad=1)
            session.add(item)
        session.commit()

# 🗑️ Eliminar un producto del carrito
def eliminar_item_del_carrito(id_users: int, id_producto: int) -> None:
    with Session(engine) as session:
        item = session.exec(
            select(Carrito).where(
                Carrito.id_users == id_users,
                Carrito.id_producto == id_producto
            )
        ).first()
        if item:
            if item.cantidad > 1:
                item.cantidad -= 1
                session.add(item)
            else:
                session.delete(item)
            session.commit()

# 🧹 Vaciar todo el carrito
def vaciar_carrito(id_users: int) -> None:
    with Session(engine) as session:
        query = select(Carrito).where(Carrito.id_users == id_users)
        items = session.exec(query).all()
        for item in items:
            session.delete(item)
        session.commit()