from proyectofinal.repository.carrito_repository import (
    obtener_carrito_agrupado_por_usuario,
    agregar_item_al_carrito,
    eliminar_item_del_carrito,
    vaciar_carrito
)
from proyectofinal.repository.conect_db import engine
from sqlmodel import Session

# 🔍 Cargar carrito completo con productos y subtotales
def cargar_carrito_service(id_users: int) -> list[dict]:
    if not id_users:
        raise ValueError("El ID de usuario no puede ser nulo al cargar el carrito.")
    with Session(engine) as session:
        return obtener_carrito_agrupado_por_usuario(session, id_users)

# ✅ Agregar producto al carrito
def agregar_producto_service(id_users: int, id_producto: int) -> None:
    if not id_users:
        raise ValueError("El ID de usuario no puede ser nulo al agregar productos.")
    agregar_item_al_carrito(id_users, id_producto)

# 🗑️ Eliminar producto del carrito
def eliminar_producto_service(id_users: int, id_producto: int) -> None:
    if not id_users:
        raise ValueError("El ID de usuario no puede ser nulo al eliminar productos.")
    eliminar_item_del_carrito(id_users, id_producto)

# 🧹 Finalizar compra (vaciar carrito)
def finalizar_compra_service(id_users: int) -> None:
    if not id_users:
        raise ValueError("El ID de usuario no puede ser nulo al finalizar la compra.")
    vaciar_carrito(id_users)