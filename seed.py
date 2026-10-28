"""Seed inicial: administrador y catalogo de ejemplo.

Uso:
    .\\.venv\\Scripts\\python.exe seed.py

Es idempotente: si el admin, una categoria o un producto ya existen, no los
duplica. El admin sale de ``ADMIN_EMAIL`` / ``ADMIN_PASSWORD`` en ``.env``
(D-013); no hay credenciales por defecto en el codigo.
"""

from __future__ import annotations

import os
from decimal import Decimal

from dotenv import load_dotenv
from sqlmodel import Session, select

from app.model.categoria_modelo import Categoria
from app.model.product_model import Producto
from app.model.stock_model import Stocks
from app.repository.conect_db import get_session
from app.service.auth_servicio import ErrorDeRegistro, crear_admin_si_no_existe

load_dotenv()

ADMIN_NOMBRE = os.getenv("ADMIN_NOMBRE", "Administrador")

CATEGORIAS = ["Running", "Urbano", "Formal", "Outdoor", "Infantil", "Verano"]

PRODUCTOS = [
    {
        "nombre": "Zapatilla Running Air",
        "descripcion": "Amortiguacion para entrenamiento diario",
        "precio": Decimal("89999.00"),
        "marca": "Nike",
        "categoria": "Running",
        "imagen": "https://picsum.photos/seed/running-air/600/600",
        "variantes": [("Negro", "40", 3), ("Negro", "42", 5), ("Blanco", "42", 3)],
    },
    {
        "nombre": "Zapatilla Urbana Classic",
        "descripcion": "Diseno urbano con suela de goma",
        "precio": Decimal("74999.00"),
        "marca": "Adidas",
        "categoria": "Urbano",
        "imagen": "https://picsum.photos/seed/urbana-classic/600/600",
        "variantes": [("Blanco", "39", 2), ("Blanco", "40", 4), ("Negro", "40", 2)],
    },
    {
        "nombre": "Zapato Formal Cuero",
        "descripcion": "Cuero natural para ocasiones formales",
        "precio": Decimal("65999.00"),
        "marca": "Bata",
        "categoria": "Formal",
        "imagen": "https://picsum.photos/seed/formal-cuero/600/600",
        "variantes": [("Marron", "41", 2), ("Marron", "42", 1)],
    },
    {
        "nombre": "Bota Trekking Andes",
        "descripcion": "Impermeable, para montana y senderismo",
        "precio": Decimal("129999.00"),
        "marca": "Columbia",
        "categoria": "Outdoor",
        "imagen": "https://picsum.photos/seed/trekking-andes/600/600",
        "variantes": [("Gris", "42", 2), ("Gris", "43", 3)],
    },
    {
        "nombre": "Zapatilla Nino Sport",
        "descripcion": "Liviana y flexible para uso escolar",
        "precio": Decimal("39999.00"),
        "marca": "Topper",
        "categoria": "Infantil",
        "imagen": "https://picsum.photos/seed/nino-sport/600/600",
        "variantes": [("Azul", "31", 4), ("Azul", "32", 6)],
    },
    {
        "nombre": "Sandalia Verano",
        "descripcion": "Sandalia liviana para playa y pileta",
        "precio": Decimal("24999.00"),
        "marca": "Havaianas",
        "categoria": "Verano",
        "imagen": "https://picsum.photos/seed/sandalia-verano/600/600",
        "variantes": [("Negro", "37", 3), ("Negro", "38", 8)],
    },
]


def _admin_credentials() -> tuple[str, str]:
    email = os.getenv("ADMIN_EMAIL", "").strip()
    password = os.getenv("ADMIN_PASSWORD", "").strip()
    if not email or not password:
        raise RuntimeError(
            "Faltan ADMIN_EMAIL y ADMIN_PASSWORD en .env. Copialos de .env.example "
            "y volve a correr el seed (D-013)."
        )
    return email, password


def seed_admin() -> bool:
    """Create the bootstrap admin if it does not exist."""
    email, password = _admin_credentials()
    try:
        creado = crear_admin_si_no_existe(email=email, password=password, nombre=ADMIN_NOMBRE)
    except ErrorDeRegistro as error:
        print(f"[error] admin: {error}")
        return False

    if creado:
        print(f"[ok]   admin creado: {email}")
    else:
        print(f"[skip] admin ya existe: {email}")
    return creado


def _obtener_categoria(session: Session, nombre: str) -> Categoria:
    categoria = session.exec(select(Categoria).where(Categoria.nombre == nombre)).one_or_none()
    if categoria is not None:
        return categoria

    categoria = Categoria(nombre=nombre)
    session.add(categoria)
    session.commit()
    session.refresh(categoria)
    return categoria


def seed_categorias() -> int:
    """Create the catalog categories if they do not exist."""
    creadas = 0
    with get_session() as session:
        existentes = {c.nombre for c in session.exec(select(Categoria)).all()}
        for nombre in CATEGORIAS:
            if nombre in existentes:
                continue
            _obtener_categoria(session, nombre)
            creadas += 1

    print(f"[ok]   categorias nuevas: {creadas}")
    return creadas


def seed_productos() -> int:
    """Create demo products with their variants if they do not exist."""
    creados = 0
    with get_session() as session:
        for data in PRODUCTOS:
            existente = session.exec(
                select(Producto).where(
                    Producto.nombre == data["nombre"],
                    Producto.marca == data["marca"],
                )
            ).first()
            if existente is not None:
                print(f"[skip] producto ya existe: {data['nombre']}")
                continue

            categoria = _obtener_categoria(session, data["categoria"])
            producto = Producto(
                nombre=data["nombre"],
                descripcion=data["descripcion"],
                precio=data["precio"],
                marca=data["marca"],
                categoria_id=categoria.id,
                imagen=data["imagen"],
            )
            session.add(producto)
            session.commit()
            session.refresh(producto)

            for color, talle, cantidad in data["variantes"]:
                session.add(
                    Stocks(
                        producto_id=producto.id,
                        color=color,
                        talle=talle,
                        cantidad_disponible=cantidad,
                    )
                )
            session.commit()

            creados += 1
            print(f"[ok]   producto creado: {producto.nombre} (id={producto.id})")

    return creados


def main() -> None:
    print("--- Seed inicial ---")
    seed_admin()
    seed_categorias()
    creados = seed_productos()
    print("--------------------")
    print(f"Productos nuevos: {creados}")


if __name__ == "__main__":
    main()
