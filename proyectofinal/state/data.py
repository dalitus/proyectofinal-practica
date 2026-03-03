from typing import List, Dict, Optional
from pydantic import BaseModel

class PedidoData(BaseModel):
    id_pedido: int
    id_users: int
    estado: str
    total: float
    fecha_pedido: str
    fecha_entrega: Optional[str] = None
    nombre_usuario: str
    direccion: Optional[str] = None
    productos_json: List[Dict]   # 👈 lista de diccionarios

class PedidoAdminData(BaseModel):
    id_pedido: int
    id_users: int
    nombre_usuario: str
    estado: str
    total: float
    fecha_pedido: str
    fecha_entrega: Optional[str] = None
    productos_json: List[Dict] = []   # 👈 también lista
    direccion: Optional[str] = None
    numero: Optional[str] = None
    departamento: Optional[str] = None
    codigo_postal: Optional[str] = None
    ciudad: Optional[str] = None
    provincia: Optional[str] = None