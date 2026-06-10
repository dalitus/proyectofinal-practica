# proyectofinal/service/producto_servicio.py

import os
from typing import Optional
from sqlmodel import Session
from proyectofinal.service.gdrive_service import upload_image_to_drive
from proyectofinal.model.product_model import Producto
from proyectofinal.repository import producto_repocitory
from proyectofinal.repository.conect_db import get_session

# Obtener todos los productos (con stocks eager-loaded)
def obtener_productos() -> list[Producto]:
    return producto_repocitory.get_all_productos()

# Obtener producto por ID
def obtener_producto_por_id(producto_id: int) -> Producto | None:
    return producto_repocitory.get_producto_by_id(producto_id)

# Crear nuevo producto
def crear_producto(
    nombre: str,
    descripcion: str,
    precio: float,
    marca: str,
    categoria: str,
    talle: str,
    imagen: Optional[str] = None,
) -> Producto:
    if not nombre or precio is None:
        raise ValueError("Nombre y precio son obligatorios.")

    imagen_url: Optional[str] = None
    try:
        print(f"[PRODUCTO] crear_producto: imagen entrada={imagen}")
        if imagen and os.path.isfile(imagen):
            folder_id = os.getenv("GDRIVE_FOLDER_ID")
            print(f"[PRODUCTO] Subiendo imagen local a Drive. folder_id={folder_id}")
            imagen_url = upload_image_to_drive(imagen, folder_id=folder_id, producto_nombre=nombre)
            print(f"[PRODUCTO] URL recibida de Drive: {imagen_url}")
        else:
            imagen_url = imagen
    except Exception as e:
        import traceback
        print(f"[PRODUCTO] Error subiendo imagen: {e}")
        traceback.print_exc()
        imagen_url = imagen if (isinstance(imagen, str) and imagen.startswith("http")) else ""

    nuevo = Producto(
        nombre=nombre,
        descripcion=descripcion,
        precio=precio,
        marca=marca,
        categoria=categoria,
        talle=talle,
        imagen=imagen_url,
    )
    return producto_repocitory.create_producto(nuevo)

# Editar producto existente
def editar_producto(producto_id: int, data: dict) -> bool:
    producto = obtener_producto_por_id(producto_id)
    if not producto:
        return False

    for campo, valor in data.items():
        if hasattr(producto, campo) and valor is not None and valor != "":
            if campo == "imagen":
                try:
                    print(f"[PRODUCTO] editar_producto: campo imagen valor={valor}")
                    if valor and os.path.isfile(valor):
                        folder_id = os.getenv("GDRIVE_FOLDER_ID")
                        print(f"[PRODUCTO] Subiendo imagen local a Drive. folder_id={folder_id}")
                        valor = upload_image_to_drive(valor, folder_id=folder_id, producto_nombre=producto.nombre)
                        print(f"[PRODUCTO] URL recibida de Drive: {valor}")
                except Exception:
                    print("[PRODUCTO] Error subiendo imagen, se mantiene valor.")
            setattr(producto, campo, valor)

    with get_session() as s:
        s.add(producto)
        s.commit()
        s.refresh(producto)
    return True

# Eliminar producto por ID
def eliminar_producto(producto_id: int) -> bool:
    return producto_repocitory.delete_producto(producto_id)

# Buscar productos por nombre
def buscar_productos(nombre: str) -> list[Producto]:
    return producto_repocitory.buscar_productos_por_nombre(nombre)

# Búsqueda general por texto
def buscar_productos_por_texto(texto: str) -> list[Producto]:
    return producto_repocitory.buscar_productos_por_texto(texto)