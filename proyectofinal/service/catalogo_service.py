from proyectofinal.repository.catalogo_repository import get_all_productos, buscar_productos_por_texto
from proyectofinal.model.product_model import Producto

def producto_to_dict(p: Producto) -> dict:
    total = 0
    if hasattr(p, "stocks") and p.stocks:
        total = sum(s.cantidad_disponible for s in p.stocks)
    elif hasattr(p, "stock") and p.stock:
        total = p.stock.cantidad_disponible

    return {
        "id": p.id,   # 👈 ahora usamos id
        "nombre": p.nombre,
        "descripcion": p.descripcion,
        "precio": float(p.precio),
        "marca": p.marca,
        "categoria": p.categoria,
        "talle": p.talle,
        "imagen": p.imagen or "",
        "cantidad": total,
    }
def obtener_catalogo() -> list[dict]:
    productos = [producto_to_dict(p) for p in get_all_productos()]
    # solo incluir productos con stock > 0
    return [p for p in productos if p["cantidad"] > 0]

def buscar_en_catalogo(texto: str) -> list[dict]:
    productos = [producto_to_dict(p) for p in buscar_productos_por_texto(texto)]
    return [p for p in productos if p["cantidad"] > 0]