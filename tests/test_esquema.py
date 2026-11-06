"""Tests del esquema: variantes, carrito, pedidos y snapshot (D-009, D-029)."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest
from reflex_local_auth import LocalUser
from sqlalchemy.exc import DatabaseError, IntegrityError
from sqlmodel import Session, select

from app.model import (
    Carrito,
    Categoria,
    Pedido,
    PedidoItem,
    Producto,
    Stocks,
    UserProfile,
)

TABLAS_ESPERADAS = {
    "categorias",
    "carritos",
    "consultas",
    "localauthsession",
    "localuser",
    "pedido_items",
    "pedidos",
    "productos",
    "stocks",
    "ubicacionlocal",
    "user_profiles",
}


def crear_producto(session: Session, nombre: str = "Zapatilla") -> Producto:
    categoria = Categoria(nombre=f"Categoria {nombre}")
    session.add(categoria)
    session.commit()
    session.refresh(categoria)

    producto = Producto(
        nombre=nombre,
        descripcion="desc",
        marca="Marca",
        precio=Decimal("10000.00"),
        categoria_id=categoria.id,
    )
    session.add(producto)
    session.commit()
    session.refresh(producto)
    return producto


def crear_variante(
    session: Session, producto: Producto, color: str, talle: str, stock: int = 5
) -> Stocks:
    variante = Stocks(
        producto_id=producto.id,
        color=color,
        talle=talle,
        cantidad_disponible=stock,
    )
    session.add(variante)
    session.commit()
    session.refresh(variante)
    return variante


def crear_usuario(session: Session, username: str = "comprador@example.com") -> LocalUser:
    user = LocalUser(
        username=username,
        password_hash=LocalUser.hash_password("Clave-12345"),
        enabled=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def test_tablas_del_esquema(session: Session) -> None:
    from sqlmodel import SQLModel

    assert set(SQLModel.metadata.tables) == TABLAS_ESPERADAS


def test_variante_es_unica_por_producto_color_y_talle(session: Session) -> None:
    producto = crear_producto(session)
    crear_variante(session, producto, "negro", "38")

    with pytest.raises(IntegrityError):
        session.add(
            Stocks(
                producto_id=producto.id,
                color="negro",
                talle="38",
                cantidad_disponible=1,
            )
        )
        session.commit()
    session.rollback()


def test_mismo_color_con_otro_talle_es_otra_variante(session: Session) -> None:
    producto = crear_producto(session)
    crear_variante(session, producto, "negro", "38")
    crear_variante(session, producto, "negro", "39")

    variantes = session.exec(select(Stocks).where(Stocks.producto_id == producto.id)).all()
    assert len(variantes) == 2


def test_stock_negativo_se_rechaza(session: Session) -> None:
    producto = crear_producto(session)

    with pytest.raises(DatabaseError):
        session.add(
            Stocks(producto_id=producto.id, color="negro", talle="38", cantidad_disponible=-1)
        )
        session.commit()
    session.rollback()


def test_carrito_una_linea_por_usuario_y_variante(session: Session) -> None:
    producto = crear_producto(session)
    variante = crear_variante(session, producto, "negro", "38")
    user = crear_usuario(session)

    session.add(Carrito(usuario_id=user.id, variante_id=variante.id_stock, cantidad=1))
    session.commit()

    with pytest.raises(IntegrityError):
        session.add(Carrito(usuario_id=user.id, variante_id=variante.id_stock, cantidad=2))
        session.commit()
    session.rollback()


def test_carrito_exige_usuario_existente(session: Session) -> None:
    producto = crear_producto(session)
    variante = crear_variante(session, producto, "negro", "38")

    with pytest.raises(IntegrityError):
        session.add(Carrito(usuario_id=999999, variante_id=variante.id_stock, cantidad=1))
        session.commit()
    session.rollback()


def test_pedido_guarda_snapshot_de_la_compra(session: Session) -> None:
    producto = crear_producto(session)
    variante = crear_variante(session, producto, "negro", "38")
    user = crear_usuario(session)

    precio = Decimal("10000.00")
    pedido = Pedido(usuario_id=user.id, total=precio * 2, estado="en espera")
    session.add(pedido)
    session.commit()
    session.refresh(pedido)

    item = PedidoItem(
        pedido_id=pedido.id_pedido,
        variante_id=variante.id_stock,
        color=variante.color,
        talle=variante.talle,
        cantidad=2,
        precio_unitario=precio,
    )
    session.add(item)
    session.commit()
    session.refresh(item)

    # El producto cambia de precio y se desactiva: el pedido no cambia.
    producto.precio = Decimal("99999.00")
    producto.activo = False
    session.add(producto)
    session.commit()

    guardado = session.exec(
        select(PedidoItem).where(PedidoItem.pedido_id == pedido.id_pedido)
    ).one()
    assert guardado.precio_unitario == precio
    assert guardado.color == "negro"
    assert guardado.talle == "38"
    assert guardado.cantidad == 2


def test_perfil_es_unico_por_usuario(session: Session) -> None:
    user = crear_usuario(session)
    session.add(
        UserProfile(
            local_user_id=user.id,
            nombre="Ana",
            email="ana@example.com",
            is_admin=True,
        )
    )
    session.commit()

    with pytest.raises(IntegrityError):
        session.add(
            UserProfile(
                local_user_id=user.id,
                nombre="Otra",
                email="otra@example.com",
            )
        )
        session.commit()
    session.rollback()


def _revisiones() -> list[tuple[str, str | None]]:
    import re

    revisiones = []
    for archivo in Path("alembic/versions").glob("*.py"):
        texto = archivo.read_text(encoding="utf-8")
        revision = re.search(r"^revision: str = [\"']([^\"']+)[\"']", texto, re.MULTILINE)
        padre = re.search(r"^down_revision[^=]*= (None|[\"']([^\"']+)[\"'])", texto, re.MULTILINE)
        if revision:
            down = (
                None if padre and padre.group(1) == "None" else (padre.group(2) if padre else None)
            )
            revisiones.append((revision.group(1), down))
    return revisiones


def test_hay_un_solo_head_de_alembic() -> None:
    revisiones = _revisiones()
    assert revisiones, "no hay migraciones"

    padres = {down for _, down in revisiones if down}
    heads = [rev for rev, _ in revisiones if rev not in padres]
    assert len(heads) == 1, f"se esperaba un head, hay {heads}"
