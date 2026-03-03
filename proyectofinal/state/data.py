from typing import List, Dict, Optional
from pydantic import BaseModel

class PedidoData(BaseModel):
    id_pedido: int
    id_users: int              # 👈 corregido, antes estaba id_usuario
    estado: str
    total: float
    fecha_pedido: str
    fecha_entrega: Optional[str] = None
    nombre_usuario: str
    direccion: Optional[str] = None
    productos_json: List[Dict]   # lista de diccionarios

class PedidoAdminData(BaseModel):
    id_pedido: int
    id_users: int              # 👈 corregido, antes estaba id_usuario
    nombre_usuario: str
    total: float
    fecha_pedido: str
    productos_json: list[dict]
    direccion: str | None = None
    numero: str | None = None
    departamento: str | None = None
    codigo_postal: str | None = None
    ciudad: str | None = None
    provincia: str | None = None
    estado: str

    # Campos nuevos
    talles: str | None = None
    colores: str | None = None