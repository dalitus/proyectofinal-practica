from proyectofinal.repository.conect_db import get_session
from proyectofinal.model.product_model import Producto

with get_session() as s:
    productos = s.exec(Producto.select()).all() if hasattr(Producto, 'select') else s.exec(Producto.__table__.select()).all()
    # Fallback if SQLModel select not available
    if not productos:
        productos = s.exec(Producto.__table__.select()).all()

    for p in productos:
        try:
            cantidad = p.stock.cantidad_disponible if getattr(p, 'stock', None) else None
        except Exception:
            cantidad = None
        print(f"ID={getattr(p, 'id_producto', getattr(p, 'id', None))} Nombre={p.nombre} Talle={p.talle} Cantidad={cantidad}")
