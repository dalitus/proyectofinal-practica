from proyectofinal.repository.catalogo_repository import get_all_productos, buscar_productos_por_texto
from proyectofinal.model.product_model import Producto

def producto_to_dict(p: Producto) -> dict:
    return {
        "id_producto": p.id_producto,
        "nombre": p.nombre,
        "descripcion": p.descripcion,
        "precio": float(p.precio),
        "marca": p.marca,
        "categoria": p.categoria,
        "talle": p.talle,
        "imagen": p.imagen or "",
        # intentar obtener cantidad desde relación stock si existe
        "cantidad": getattr(getattr(p, 'stock', None), 'cantidad_disponible', None)
    }

def obtener_catalogo() -> list[dict]:
    # Sólo incluir productos con cantidad disponible > 0
    productos = [producto_to_dict(p) for p in get_all_productos()]
    return [p for p in productos if (p.get("cantidad") is not None and int(p.get("cantidad", 0)) > 0)]

def buscar_en_catalogo(texto: str) -> list[dict]:
    productos = [producto_to_dict(p) for p in buscar_productos_por_texto(texto)]
    return [p for p in productos if (p.get("cantidad") is not None and int(p.get("cantidad", 0)) > 0)]