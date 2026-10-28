from sqlmodel import Session, select
from app.model.pedido_model import Pedido
from app.model.users_model import Users
from app.model.carrito_model import Carrito
from app.model.product_model import Producto
from app.repository.conect_db import engine
import json


def obtener_productos_carrito_usuario(id_usuario: int) -> str:
    """Obtener productos del carrito del usuario como JSON"""
    with Session(engine) as session:
        items_carrito = session.exec(
            select(Carrito, Producto)
            .where(Carrito.usuario_id == id_usuario)              # 👈 corregido
            .join(Producto, Carrito.producto_id == Producto.id)   # 👈 corregido
        ).all()

        productos = []
        for carrito, producto in items_carrito:
            cantidad = getattr(carrito, "cantidad", 1)
            precio = float(producto.precio) if producto.precio else 0.0
            productos.append({
                "id_producto": producto.id,                       # 👈 corregido
                "nombre": producto.nombre,
                "cantidad": cantidad,
                "precio": precio,
                "subtotal": precio * cantidad,
                "imagen": getattr(producto, "imagen", "")
            })

        return json.dumps(productos)


def crear_pedido(
    id_usuario: int,
    total: float,
    fecha_pedido: str,
    productos_json: str = "",
    direccion: str = None,
    numero: str = None,
    departamento: str = None,
    codigo_postal: str = None,
    ciudad: str = None,
    provincia: str = None,
    talles: str = None,
    colores: str = None
) -> dict:
    """Crear un nuevo pedido con datos de ubicación"""
    with Session(engine) as session:
        nuevo_pedido = Pedido(
            id_usuario=id_usuario,          # 👈 corregido
            estado="en espera",
            total=total,
            fecha_pedido=fecha_pedido,
            productos_json=productos_json,
            direccion=direccion,
            numero=numero,
            departamento=departamento,
            codigo_postal=codigo_postal,
            ciudad=ciudad,
            provincia=provincia,
            talles=talles,
            colores=colores
        )
        session.add(nuevo_pedido)
        session.commit()
        session.refresh(nuevo_pedido)

        return {
            "id_pedido": nuevo_pedido.id_pedido,
            "estado": nuevo_pedido.estado,
            "total": nuevo_pedido.total,
            "fecha_pedido": nuevo_pedido.fecha_pedido,
            "productos_json": nuevo_pedido.productos_json,
            "direccion": nuevo_pedido.direccion,
            "numero": nuevo_pedido.numero,
            "departamento": nuevo_pedido.departamento,
            "codigo_postal": nuevo_pedido.codigo_postal,
            "ciudad": nuevo_pedido.ciudad,
            "provincia": nuevo_pedido.provincia,
            "talles": nuevo_pedido.talles,
            "colores": nuevo_pedido.colores,
        }


def obtener_pedidos_usuario(id_usuario: int) -> list[dict]:
    """Obtener todos los pedidos de un usuario con datos del usuario"""
    with Session(engine) as session:
        pedidos = session.exec(
            select(Pedido).where(Pedido.id_usuario == id_usuario)   # 👈 corregido
        ).all()
        resultado = []
        for p in pedidos:
            usuario = session.exec(
                select(Users).where(Users.id == p.id_usuario)       # 👈 corregido
            ).first()

            resultado.append({
                "id_pedido": p.id_pedido,
                "id_usuario": p.id_usuario,                        # 👈 corregido
                "nombre_usuario": f"{usuario.nombre} {usuario.apellido}" if usuario else "N/A",
                "direccion_usuario": usuario.direccion if usuario else "N/A",
                "estado": p.estado,
                "total": p.total,
                "fecha_pedido": p.fecha_pedido,
                "fecha_entrega": p.fecha_entrega,
                "productos_json": p.productos_json if p.productos_json else "[]",
                "direccion": p.direccion,
                "numero": p.numero,
                "departamento": p.departamento,
                "codigo_postal": p.codigo_postal,
                "ciudad": p.ciudad,
                "provincia": p.provincia,
                "talles": p.talles,
                "colores": p.colores,
            })
        return resultado


def obtener_todos_pedidos() -> list[dict]:
    """Obtener TODOS los pedidos (para admin) con datos del usuario"""
    with Session(engine) as session:
        pedidos = session.exec(select(Pedido)).all()
        resultado = []
        for p in pedidos:
            usuario = session.exec(
                select(Users).where(Users.id == p.id_usuario)       # 👈 corregido
            ).first()

            try:
                productos = json.loads(p.productos_json) if p.productos_json else []
            except Exception:
                productos = []
            resultado.append({
                "id_pedido": p.id_pedido,
                "id_usuario": p.id_usuario,                        # 👈 corregido
                "nombre_usuario": f"{usuario.nombre} {usuario.apellido}" if usuario else "N/A",
                "direccion_usuario": usuario.direccion if usuario else "N/A",
                "estado": p.estado,
                "total": p.total,
                "fecha_pedido": p.fecha_pedido,
                "fecha_entrega": p.fecha_entrega,
                "productos_json": productos,
                "direccion": p.direccion,
                "numero": p.numero,
                "departamento": p.departamento,
                "codigo_postal": p.codigo_postal,
                "ciudad": p.ciudad,
                "provincia": p.provincia,
                "talles": p.talles,
                "colores": p.colores,
            })
        return resultado


def obtener_pedido_por_id(id_pedido: int) -> dict | None:
    """Obtener un pedido específico con productos y ubicación"""
    with Session(engine) as session:
        pedido = session.exec(
            select(Pedido).where(Pedido.id_pedido == id_pedido)
        ).first()

        if not pedido:
            return None

        usuario = session.exec(
            select(Users).where(Users.id == pedido.id_usuario)      # 👈 corregido
        ).first()

        return {
            "id_pedido": pedido.id_pedido,
            "id_usuario": pedido.id_usuario,                        # 👈 corregido
            "nombre_usuario": f"{usuario.nombre} {usuario.apellido}" if usuario else "N/A",
            "direccion_usuario": usuario.direccion if usuario else "N/A",
            "estado": pedido.estado,
            "total": pedido.total,
            "fecha_pedido": pedido.fecha_pedido,
            "fecha_entrega": pedido.fecha_entrega,
            "productos_json": pedido.productos_json if pedido.productos_json else "[]",
            "direccion": pedido.direccion,
            "numero": pedido.numero,
            "departamento": pedido.departamento,
            "codigo_postal": pedido.codigo_postal,
            "ciudad": pedido.ciudad,
            "provincia": pedido.provincia,
            "talles": pedido.talles,
            "colores": pedido.colores,
        }


def actualizar_estado_pedido(id_pedido: int, nuevo_estado: str) -> bool:
    """Actualizar el estado de un pedido"""
    if nuevo_estado not in ["en espera", "enviado", "entregado"]:
        raise ValueError("Estado inválido")

    with Session(engine) as session:
        pedido = session.exec(
            select(Pedido).where(Pedido.id_pedido == id_pedido)
        ).first()

        if not pedido:
            return False

        pedido.estado = nuevo_estado
        session.add(pedido)
        session.commit()
        return True


def eliminar_pedido(id_pedido: int) -> bool:
    """Eliminar un pedido"""
    with Session(engine) as session:
        pedido = session.exec(
            select(Pedido).where(Pedido.id_pedido == id_pedido)
        ).first()

        if not pedido:
            return False

        session.delete(pedido)
        session.commit()
        return True
