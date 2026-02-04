import reflex as rx
from sqlmodel import Session
from proyectofinal.repository.carrito_repository import (
    obtener_carrito_completo_por_usuario,
    vaciar_carrito,
    eliminar_item_del_carrito,
    agregar_item_al_carrito
)
from proyectofinal.repository.conect_db import engine
from collections import Counter

class GlobalState(rx.State):
    user_id: int = 0
    logeado: bool = False
    productos_carrito: list[dict] = []
    total: float = 0.0
    mensaje_compra: str = ""

    @rx.event
    def login(self, usuario_id: int):
        self.user_id = usuario_id
        self.logeado = True
        self.cargar_carrito_agrupado()

    @rx.event
    def logout(self):
        self.user_id = 0
        self.logeado = False
        self.productos_carrito = []
        self.total = 0.0
        self.mensaje_compra = "👋 Sesión cerrada correctamente."

    @rx.event
    def cargar_carrito_agrupado(self):
        with Session(engine) as db:
            resultados = obtener_carrito_completo_por_usuario(db, self.user_id)
            self.productos_carrito = [
                {
                    "id_producto": producto.id_producto,
                    "nombre": producto.nombre,
                    "precio": producto.precio,
                    "imagen": producto.imagen
                }
                for carrito, producto, usuario in resultados
            ]
            self.total = sum(p["precio"] for p in self.productos_carrito)

    @rx.event
    def agregar_carrito_con_id(self, id_producto: int):
        if self.user_id == 0:
            self.mensaje_compra = "⚠️ Debes iniciar sesión para agregar productos."
            return
        agregar_item_al_carrito(self.user_id, id_producto)
        self.cargar_carrito_agrupado()

    @rx.event
    def eliminar_producto(self, id_producto: int):
        eliminar_item_del_carrito(self.user_id, id_producto)
        self.cargar_carrito_agrupado()

    @rx.event
    def vaciar_carrito_completo(self):
        vaciar_carrito(self.user_id)
        self.productos_carrito = []
        self.total = 0.0
        self.mensaje_compra = "🧹 Carrito vaciado correctamente."

    @rx.event
    def finalizar_compra(self):
        vaciar_carrito(self.user_id)
        self.productos_carrito = []
        self.total = 0.0
        self.mensaje_compra = "✅ ¡Compra finalizada con éxito!"

    @rx.var
    def productos_agrupados(self) -> list[dict]:
        contador = Counter(p["id_producto"] for p in self.productos_carrito)
        agrupados = []
        vistos = set()

        for producto in self.productos_carrito:
            pid = producto["id_producto"]
            if pid not in vistos:
                vistos.add(pid)
                agrupados.append({
                    "id_producto": pid,
                    "nombre": producto["nombre"],
                    "precio": producto["precio"],
                    "imagen": producto["imagen"],
                    "cantidad": contador[pid],
                    "subtotal": producto["precio"] * contador[pid]
                })
        return agrupados