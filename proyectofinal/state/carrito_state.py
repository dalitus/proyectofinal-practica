import reflex as rx
from sqlmodel import Session
from collections import Counter
from proyectofinal.repository.carrito_repository import (
    get_items_por_usuario,
    agregar_item_al_carrito,
    eliminar_item_del_carrito,
    vaciar_carrito,
    obtener_carrito_agrupado_por_usuario,
    obtener_carrito_completo_por_usuario
)
from proyectofinal.repository.conect_db import engine
from proyectofinal.state.users_state import UsersState
from proyectofinal.repository.consulta_repocitory import crear_consulta_repo

class CarritoState(rx.State):
    productos_carrito: list[dict] = []
    total: float = 0.0
    mensaje_compra: str = ""
    
    # Estados para el modal de ubicación
    mostrar_modal_ubicacion: bool = False
    direccion: str = ""
    numero: str = ""
    departamento: str = ""
    codigo_postal: str = ""
    ciudad: str = ""
    provincia: str = ""
    
    @rx.event
    def abrir_modal_ubicacion(self):
        """Abre el modal para solicitar datos de ubicación"""
        if not self.productos_carrito:
            self.mensaje_compra = "No hay productos en el carrito."
            return
        self.mostrar_modal_ubicacion = True
    
    @rx.event
    def cerrar_modal_ubicacion(self):
        """Cierra el modal de ubicación"""
        self.mostrar_modal_ubicacion = False
    
    @rx.event
    def limpiar_ubicacion(self):
        """Limpia los datos de ubicación"""
        self.direccion = ""
        self.numero = ""
        self.departamento = ""
        self.codigo_postal = ""
        self.ciudad = ""
        self.provincia = ""

    @rx.event
    async def finalizar_compra_con_ubicacion(self):
        """Finaliza la compra con los datos de ubicación"""
        user_id = await UsersState.get_user_id()
        if not user_id:
            self.mensaje_compra = "Debes iniciar sesión para finalizar la compra."
            return

        if not self.productos_carrito:
            self.mensaje_compra = "No hay productos en el carrito."
            return
        
        # Validar que los datos de ubicación estén completos
        if not self.direccion or not self.ciudad or not self.provincia:
            self.mensaje_compra = "Por favor completa todos los datos de ubicación requeridos."
            return

        # Armar detalle de compra
        detalle = "\n".join(
            f"- {p['nombre']} x{p['cantidad']} = ${p['subtotal']}" for p in self.productos_carrito
        )

        mensaje = f"El usuario {user_id} realizó una compra con los siguientes productos:\n{detalle}"

        # Registrar como consulta automática
        crear_consulta_repo(
            id_users=user_id,
            asunto="Compra realizada",
            mensaje=mensaje
        )
        
        # Crear pedido en la tabla pedidos
        try:
            from proyectofinal.service.pedido_service import crear_pedido
            from datetime import datetime
            import json
            
            total_compra = sum(p["subtotal"] for p in self.productos_carrito)
            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Convertir productos a JSON
            productos_json = json.dumps(self.productos_carrito)
            
            crear_pedido(
                id_usuario=user_id,
                total=total_compra,
                fecha_pedido=fecha_actual,
                productos_json=productos_json,
                direccion=self.direccion,
                numero=self.numero,
                departamento=self.departamento,
                codigo_postal=self.codigo_postal,
                ciudad=self.ciudad,
                provincia=self.provincia
            )
        except Exception as e:
            print(f"Error al crear pedido: {e}")
            self.mensaje_compra = f"Error al procesar el pedido: {e}"
            return

        # Vaciar carrito y mostrar mensaje
        vaciar_carrito(user_id)
        self.productos_carrito = []
        self.total = 0.0
        self.limpiar_ubicacion()
        self.mostrar_modal_ubicacion = False
        self.mensaje_compra = "✅ Compra finalizada correctamente. Gracias por tu pedido."

    @rx.event
    async def cargar_carrito_agrupado(self):
        # Limpiar mensajes previos al cargar
        self.mensaje_compra = ""
        user_id = await UsersState.get_user_id()
        if not user_id:
            self.productos_carrito = []
            self.total = 0.0
            return
        with Session(engine) as db:
            self.productos_carrito = obtener_carrito_agrupado_por_usuario(db, user_id)
            self.total = sum(p["subtotal"] for p in self.productos_carrito)

    @rx.event
    def cargar_carrito_detallado(self):
        with Session(engine) as db:
            resultados = obtener_carrito_completo_por_usuario(db, self.user_id)
            self.productos_carrito = [
                {
                    "nombre": producto.nombre,
                    "precio": producto.precio,
                    "id_producto": producto.id_producto,
                    "id_carrito": carrito.id_carrito,
                    "imagen": producto.imagen
                }
                for carrito, producto, usuario in resultados
            ]
            self.total = sum(p["precio"] for p in self.productos_carrito)

    @rx.event
    def cargar_carrito(self):
        # Limpiar mensajes cuando se carga el carrito
        self.mensaje_compra = ""
        self.productos_carrito = get_items_por_usuario(self.user_id)

    @rx.event
    async def vaciar_carrito_completo(self):
        user_id = await UsersState.get_user_id()
        if not user_id:
            self.mensaje_compra = "Debes iniciar sesión para vaciar el carrito."
            return
        vaciar_carrito(user_id)
        self.productos_carrito = []
        self.total = 0.0
        self.mensaje_compra = "Carrito vaciado correctamente."

    @rx.event
    async def eliminar_producto(self, id_producto: int):
        user_id = await UsersState.get_user_id()
        if not user_id:
            self.mensaje_compra = "Debes iniciar sesión para eliminar productos."
            return
        eliminar_item_del_carrito(user_id, id_producto)
        await self.cargar_carrito_agrupado()


    @rx.event
    async def agregar_carrito_con_id(self, id_producto: int):
        user_id = await UsersState.get_user_id()
        if not user_id:
            self.mensaje_compra = "Debes iniciar sesión para agregar productos."
            return
        agregar_item_al_carrito(user_id, id_producto)
        await self.cargar_carrito_agrupado()
        self.mensaje_compra = "Producto agregado al carrito."

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
                    "imagen": producto.get("imagen", ""),
                    "cantidad": contador[pid],
                    "subtotal": producto["precio"] * contador[pid]
                })
        return agrupados