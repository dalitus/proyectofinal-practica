"""Precio final consistente entre pantallas (T-032, D-003).

Un mismo producto tiene que mostrar el mismo string en catalogo, detalle, carrito
y pedido, y el total del pedido tiene que ser exactamente el subtotal del carrito.
Si alguien reimplementa el formato en una pagina, este test lo delata.
"""

from __future__ import annotations

from decimal import Decimal

from reflex_local_auth.local_auth import LocalUser
from sqlmodel import Session

from app.model.categoria_modelo import Categoria
from app.model.producto_modelo import Producto
from app.model.variante_modelo import Stocks
from app.service import carrito_servicio, catalogo_servicio, pedido_servicio
from app.service.formato_moneda import formatear_precio

ENTREGA = {
    "direccion": "San Martin",
    "numero": "1234",
    "departamento": "4 B",
    "codigo_postal": "1425",
    "ciudad": "CABA",
    "provincia": "Buenos Aires",
}

PRECIO = "89999.00"


def _comprador(session: Session) -> int:
    usuario = LocalUser(
        username="ana@example.com",
        password_hash=LocalUser.hash_password("secreto123"),
        enabled=True,
    )
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    usuario_id = usuario.id or 0
    session.rollback()
    return usuario_id


def _producto(session: Session) -> tuple[int, int]:
    categoria = Categoria(nombre="Running")
    session.add(categoria)
    session.commit()
    session.refresh(categoria)

    producto = Producto(
        nombre="Zapatilla Running Air",
        marca="Fermin",
        precio=Decimal(PRECIO),
        categoria_id=categoria.id,
        activo=True,
    )
    session.add(producto)
    session.commit()
    session.refresh(producto)

    variante = Stocks(
        producto_id=producto.id,
        color="Blanco",
        talle="40",
        cantidad_disponible=5,
    )
    session.add(variante)
    session.commit()
    session.refresh(variante)
    producto_id = producto.id or 0
    variante_id = variante.id_stock or 0
    session.rollback()
    return producto_id, variante_id


def test_el_mismo_producto_muestra_el_mismo_precio_en_todas_las_pantallas(
    session: Session,
) -> None:
    usuario_id = _comprador(session)
    producto_id, variante_id = _producto(session)
    esperado = formatear_precio(PRECIO)

    tarjeta = next(
        producto
        for producto in catalogo_servicio.listar_catalogo().productos
        if producto.id == producto_id
    )
    detalle = catalogo_servicio.obtener_detalle(producto_id)
    assert detalle is not None

    carrito_servicio.agregar(usuario_id, variante_id, 2)
    carrito = carrito_servicio.ver_carrito(usuario_id)

    assert tarjeta.precio == esperado
    assert detalle.precio == esperado
    assert carrito.lineas[0].precio_unitario == esperado
    assert carrito.lineas[0].subtotal == formatear_precio("179998.00")


def test_el_total_del_pedido_es_el_subtotal_del_carrito(session: Session) -> None:
    usuario_id = _comprador(session)
    _, variante_id = _producto(session)
    carrito_servicio.agregar(usuario_id, variante_id, 3)

    carrito = carrito_servicio.ver_carrito(usuario_id)
    pedido_id = pedido_servicio.confirmar_pedido(
        usuario_id,
        pedido_servicio.validar_entrega(ENTREGA),
    )
    pedido = pedido_servicio.obtener_detalle(pedido_id)

    assert pedido.total == carrito.subtotal
    assert pedido.total == formatear_precio("269997.00")
    assert pedido.lineas[0].precio_unitario == formatear_precio(PRECIO)
    assert pedido.lineas[0].subtotal == carrito.subtotal
