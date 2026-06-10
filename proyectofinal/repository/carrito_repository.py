from sqlmodel import Session, select
from proyectofinal.model.carrito_model import Carrito
from proyectofinal.model.product_model import Producto
from proyectofinal.model.users_model import Users
from proyectofinal.repository.conect_db import engine

# 🔍 Obtener carrito agrupado por producto
def obtener_carrito_agrupado_por_usuario(db: Session, usuario_id: int) -> list[dict]:
    resultados = obtener_carrito_completo_por_usuario(db, usuario_id)
    agrupados = []
    for carrito, producto, usuario in resultados:
        agrupados.append({
            "id_producto": producto.id,   # 👈 usar producto.id
            "nombre": producto.nombre,
            "precio": float(producto.precio),
            "imagen": producto.imagen,
            "cantidad": carrito.cantidad,
            "subtotal": float(producto.precio) * carrito.cantidad
        })
    return agrupados

# 🔍 Obtener carrito completo con joins
def obtener_carrito_completo_por_usuario(db: Session, usuario_id: int):
    return (
        db.query(Carrito, Producto, Users)
        .join(Producto, Carrito.producto_id == Producto.id)   # 👈 corregido
        .join(Users, Carrito.usuario_id == Users.id)
        .filter(Carrito.usuario_id == usuario_id)
        .all()
    )

# 🔍 Obtener items sin joins (solo IDs)
def get_items_por_usuario(usuario_id: int) -> list[dict]:
    with Session(engine) as session:
        resultados = session.exec(
            select(Carrito).where(Carrito.usuario_id == usuario_id)
        ).all()
        return [
            {
                "id_carrito": r.id_carrito,
                "usuario_id": r.usuario_id,
                "producto_id": r.producto_id,
                "cantidad": r.cantidad
            }
            for r in resultados
        ]

# ✅ Agregar producto al carrito
def agregar_item_al_carrito(usuario_id: int, producto_id: int) -> None:
    if usuario_id is None:
        raise ValueError("usuario_id no puede ser None al agregar al carrito.")
    with Session(engine) as session:
        item = session.exec(
            select(Carrito).where(
                Carrito.usuario_id == usuario_id,
                Carrito.producto_id == producto_id
            )
        ).first()
        if item:
            item.cantidad += 1
            session.add(item)
        else:
            item = Carrito(usuario_id=usuario_id, producto_id=producto_id, cantidad=1)
            session.add(item)
        session.commit()

# 🗑️ Eliminar un producto del carrito
def eliminar_item_del_carrito(usuario_id: int, producto_id: int) -> None:
    with Session(engine) as session:
        item = session.exec(
            select(Carrito).where(
                Carrito.usuario_id == usuario_id,
                Carrito.producto_id == producto_id
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
def vaciar_carrito(usuario_id: int) -> None:
    with Session(engine) as session:
        query = select(Carrito).where(Carrito.usuario_id == usuario_id)
        items = session.exec(query).all()
        for item in items:
            session.delete(item)
        session.commit()