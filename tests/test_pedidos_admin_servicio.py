"""Tests del listado y el detalle del panel de pedidos (T-051, D-030).

La creación del pedido se hace por SQL directo (no por el checkout) porque acá
se prueba la lectura: filtros, búsqueda, paginación y snapshot. El camino real
carrito → checkout aparece en `test_el_pedido_del_comprador_aparece_en_el_panel`.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest
from sqlmodel import Session, select

from app.model.categoria_modelo import Categoria
from app.model.pedido_item_modelo import PedidoItem
from app.model.pedido_model import Pedido
from app.model.product_model import Producto
from app.model.stock_model import Stocks
from app.service import pedido_servicio
from app.service.auth_servicio import registrar_comprador
from app.service.carrito_servicio import agregar
from app.service.pedido_servicio import (
    ESTADOS_DE_PEDIDO,
    ESTADO_INICIAL,
    ErrorDePedido,
    confirmar_pedido,
    listar_pedidos,
    obtener_detalle,
    opciones_de_estado,
    validar_entrega,
)

ENTREGA = {
    "direccion": "San Martin",
    "numero": "1234",
    "departamento": "4 B",
    "codigo_postal": "1425",
    "ciudad": "CABA",
    "provincia": "Buenos Aires",
}


def _comprador(
    *,
    email: str = "ana@example.com",
    nombre: str = "Ana",
    apellido: str = "Perez",
) -> int:
    return registrar_comprador(
        email=email,
        password="secreto123",
        nombre=nombre,
        apellido=apellido,
    ).local_user_id


def _catalogo(
    session: Session,
    *,
    nombre_producto: str = "Zapatilla Running Air",
    variantes: list[tuple[str, str, int]] | None = None,
) -> list[Stocks]:
    categoria = Categoria(nombre=f"Categoria {nombre_producto}")
    session.add(categoria)
    session.commit()
    session.refresh(categoria)

    producto = Producto(
        nombre=nombre_producto,
        marca="Fermin",
        precio=Decimal("10000.00"),
        categoria_id=categoria.id,
        activo=True,
    )
    session.add(producto)
    session.commit()
    session.refresh(producto)

    stocks: list[Stocks] = []
    for color, talle, cantidad in variantes or [("Blanco", "40", 20)]:
        variante = Stocks(
            producto_id=producto.id,
            color=color,
            talle=talle,
            cantidad_disponible=cantidad,
        )
        session.add(variante)
        stocks.append(variante)
    session.commit()
    for variante in stocks:
        session.refresh(variante)
    return stocks


def _pedido(
    session: Session,
    *,
    usuario_id: int,
    variantes: list[Stocks],
    estado: str = "en espera",
    cantidad: int = 1,
    fecha: datetime | None = None,
) -> int:
    """Insert one order with a single snapshot line."""
    pedido = Pedido(
        usuario_id=usuario_id,
        estado=estado,
        total=Decimal("10000.00") * cantidad,
        direccion="San Martin",
        numero="1234",
        departamento="4 B",
        codigo_postal="1425",
        ciudad="CABA",
        provincia="Buenos Aires",
    )
    if fecha is not None:
        pedido.fecha_pedido = fecha
    session.add(pedido)
    session.commit()
    session.refresh(pedido)

    variante = variantes[0]
    session.add(
        PedidoItem(
            pedido_id=pedido.id_pedido or 0,
            variante_id=variante.id_stock or 0,
            color=variante.color,
            talle=variante.talle,
            cantidad=cantidad,
            precio_unitario=Decimal("10000.00"),
        )
    )
    session.commit()
    session.rollback()

    return pedido.id_pedido or 0


def test_listado_trae_clientes_totales_y_unidades(session: Session) -> None:
    usuario_id = _comprador()
    variantes = _catalogo(session)
    _pedido(session, usuario_id=usuario_id, variantes=variantes, cantidad=2)

    pagina = listar_pedidos()

    assert pagina.total == 1
    assert pagina.total_paginas == 1
    assert pagina.pagina == 1
    assert len(pagina.pedidos) == 1
    pedido = pagina.pedidos[0]
    assert pedido.cliente == "Ana Perez"
    assert pedido.email == "ana@example.com"
    assert pedido.estado == "en espera"
    assert pedido.estado_etiqueta == "En espera"
    assert pedido.total == "$ 20.000,00"
    assert pedido.unidades == 2


def test_filtro_por_estado(session: Session) -> None:
    usuario_id = _comprador()
    variantes = _catalogo(session)
    _pedido(session, usuario_id=usuario_id, variantes=variantes)
    _pedido(session, usuario_id=usuario_id, variantes=variantes, estado="enviado")
    _pedido(session, usuario_id=usuario_id, variantes=variantes, estado="enviado")

    pagina = listar_pedidos(estado="enviado")

    assert pagina.total == 2
    assert pagina.filtro_estado == "enviado"
    assert {pedido.estado for pedido in pagina.pedidos} == {"enviado"}


def test_filtro_desconocido_se_ignora(session: Session) -> None:
    usuario_id = _comprador()
    variantes = _catalogo(session)
    _pedido(session, usuario_id=usuario_id, variantes=variantes, estado="cancelado")

    pagina = listar_pedidos(estado="inventado")

    assert pagina.filtro_estado == ""
    assert pagina.total == 1


def test_busqueda_por_cliente_y_email(session: Session) -> None:
    variantes = _catalogo(session)
    ana = _comprador(email="ana@example.com", nombre="Ana", apellido="Perez")
    beto = _comprador(email="beto@example.com", nombre="Beto", apellido="Gomez")
    _pedido(session, usuario_id=ana, variantes=variantes)
    _pedido(session, usuario_id=beto, variantes=variantes)

    assert [p.cliente for p in listar_pedidos(busqueda="perez").pedidos] == ["Ana Perez"]
    assert [p.cliente for p in listar_pedidos(busqueda="BETO").pedidos] == ["Beto Gomez"]


def test_busqueda_por_producto(session: Session) -> None:
    usuario_id = _comprador()
    zapatillas = _catalogo(session, nombre_producto="Zapatilla Running Air")
    botas = _catalogo(session, nombre_producto="Bota de Cuero")
    _pedido(session, usuario_id=usuario_id, variantes=zapatillas)
    _pedido(session, usuario_id=usuario_id, variantes=botas)

    pagina = listar_pedidos(busqueda="bota")

    assert pagina.total == 1
    assert obtener_detalle(pagina.pedidos[0].id).lineas[0].producto == "Bota de Cuero"


def test_busqueda_por_numero_de_pedido(session: Session) -> None:
    usuario_id = _comprador()
    variantes = _catalogo(session)
    primero = _pedido(session, usuario_id=usuario_id, variantes=variantes)
    _pedido(session, usuario_id=usuario_id, variantes=variantes)

    pagina = listar_pedidos(busqueda=str(primero))

    assert [pedido.id for pedido in pagina.pedidos] == [primero]


def test_paginacion_de_diez_y_limites(session: Session) -> None:
    usuario_id = _comprador()
    variantes = _catalogo(session)
    for _ in range(13):
        _pedido(session, usuario_id=usuario_id, variantes=variantes)

    primera = listar_pedidos(pagina=1)
    segunda = listar_pedidos(pagina=2)
    fuera_de_rango = listar_pedidos(pagina=99)

    assert primera.total == 13
    assert primera.total_paginas == 2
    assert len(primera.pedidos) == 10
    assert primera.hay_anterior is False
    assert primera.hay_siguiente is True
    assert len(segunda.pedidos) == 3
    assert segunda.hay_anterior is True
    # Un link viejo con página 99 cae en la última, no en una tabla vacía.
    assert fuera_de_rango.pagina == 2
    assert len(fuera_de_rango.pedidos) == 3


def test_detalle_con_lineas_envio_y_total(session: Session) -> None:
    usuario_id = _comprador()
    variantes = _catalogo(session, variantes=[("Blanco", "40", 20)])
    pedido_id = _pedido(
        session,
        usuario_id=usuario_id,
        variantes=variantes,
        cantidad=3,
    )

    detalle = obtener_detalle(pedido_id)

    assert detalle.id == pedido_id
    assert detalle.cliente == "Ana Perez"
    assert detalle.estado_etiqueta == "En espera"
    assert detalle.total == "$ 30.000,00"
    assert detalle.unidades == 3
    assert detalle.envio == "San Martin 1234, 4 B, CABA, Buenos Aires, CP 1425"
    assert len(detalle.lineas) == 1
    linea = detalle.lineas[0]
    assert linea.producto == "Zapatilla Running Air"
    assert (linea.color, linea.talle, linea.cantidad) == ("Blanco", "40", 3)
    assert linea.precio_unitario == "$ 10.000,00"
    assert linea.subtotal == "$ 30.000,00"


def test_detalle_de_pedido_inexistente_falla() -> None:
    with pytest.raises(ErrorDePedido) as error:
        obtener_detalle(9999)

    assert "No existe el pedido #9999" in str(error.value)


def test_las_acciones_del_detalle_salen_del_ciclo_de_vida() -> None:
    """La pagina pinta solo transiciones validas; no inventa botones (T-044)."""
    assert pedido_servicio.estados_siguientes("en espera") == [
        {"valor": "enviado", "texto": "Enviado"},
        {"valor": "cancelado", "texto": "Cancelado"},
    ]
    assert [opcion["valor"] for opcion in pedido_servicio.estados_siguientes("enviado")] == [
        "entregado",
        "cancelado",
    ]
    assert pedido_servicio.estados_siguientes("entregado") == []
    assert pedido_servicio.estados_siguientes("cancelado") == []
    assert pedido_servicio.estados_siguientes("inventado") == []


def test_el_filtro_usa_los_estados_del_ciclo_de_vida() -> None:
    """El panel no inventa estados: ofrece los mismos de TRANSICIONES (T-044)."""
    assert [opcion["valor"] for opcion in opciones_de_estado()] == list(ESTADOS_DE_PEDIDO)
    assert [opcion["texto"] for opcion in opciones_de_estado()] == [
        "En espera",
        "Enviado",
        "Entregado",
        "Cancelado",
    ]


def test_el_pedido_del_comprador_aparece_en_el_panel(session: Session) -> None:
    """Compra real por carrito + checkout, leída por el listado del admin."""
    usuario_id = _comprador(email="demo@example.com", nombre="Demo", apellido="Compra")
    variantes = _catalogo(session)
    agregar(usuario_id, variantes[0].id_stock or 0, 2)
    pedido_id = confirmar_pedido(usuario_id, validar_entrega(ENTREGA))

    pagina = listar_pedidos(busqueda="demo@example.com")

    assert [pedido.id for pedido in pagina.pedidos] == [pedido_id]
    assert pagina.pedidos[0].unidades == 2
    assert obtener_detalle(pedido_id).unidades == 2
    # El estado del pedido recién creado es el inicial del ciclo de vida.
    assert pagina.pedidos[0].estado == ESTADO_INICIAL
    assert pedido_servicio.etiqueta_de_estado(ESTADO_INICIAL) == "En espera"
