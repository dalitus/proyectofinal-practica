from app.repository.carrito_repository import (
    obtener_carrito_agrupado_por_usuario,
    agregar_item_al_carrito,
    eliminar_item_del_carrito,
    vaciar_carrito
)
from app.repository.conect_db import engine
from sqlmodel import Session


def cargar_carrito_service(usuario_id: int | None) -> list[dict]:
    print("👉 cargar_carrito_service recibió usuario_id:", usuario_id)  # Depuración
    if usuario_id is None or usuario_id == 0:
        raise ValueError("El ID de usuario no puede ser nulo al cargar el carrito.")
    with Session(engine) as session:
        return obtener_carrito_agrupado_por_usuario(session, usuario_id)


def agregar_producto_service(usuario_id: int | None, producto_id: int) -> None:
    print("👉 agregar_producto_service recibió usuario_id:", usuario_id, "producto:", producto_id)  # Depuración
    if usuario_id is None or usuario_id == 0:
        raise ValueError("El ID de usuario no puede ser nulo al agregar productos.")
    agregar_item_al_carrito(usuario_id, producto_id)


def eliminar_producto_service(usuario_id: int | None, producto_id: int) -> None:
    print("👉 eliminar_producto_service recibió usuario_id:", usuario_id, "producto:", producto_id)  # Depuración
    if usuario_id is None or usuario_id == 0:
        raise ValueError("El ID de usuario no puede ser nulo al eliminar productos.")
    eliminar_item_del_carrito(usuario_id, producto_id)


def finalizar_compra_service(usuario_id: int | None) -> None:
    print("👉 finalizar_compra_service recibió usuario_id:", usuario_id)  # Depuración
    if usuario_id is None or usuario_id == 0:
        raise ValueError("El ID de usuario no puede ser nulo al finalizar la compra.")
    vaciar_carrito(usuario_id)