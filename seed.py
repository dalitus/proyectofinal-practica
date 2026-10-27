"""Seed inicial: administrador y productos de ejemplo.

Uso:
    .\\venv\\Scripts\\python.exe seed.py

Es idempotente: si el admin o un producto ya existen, no los duplica.
"""

from decimal import Decimal

from sqlmodel import select

from proyectofinal.model.gerente_model import Gerente
from proyectofinal.model.product_model import Producto
from proyectofinal.model.stock_model import Stocks
from proyectofinal.repository.conect_db import get_session
from proyectofinal.service.security import hash_password

ADMIN_NOMBRE = "Administrador"
ADMIN_EMAIL = "admin@zapateria.com"
ADMIN_PASSWORD = "admin123"
ADMIN_TELEFONO = "3497657610"

PRODUCTOS = [
    {
        "nombre": "Zapatilla Running Air",
        "descripcion": "Amortiguacion para entrenamiento diario",
        "precio": Decimal(89999),
        "marca": "Nike",
        "categoria": "Running",
        "talle": "42",
        "imagen": "https://picsum.photos/seed/running-air/600/600",
        "stocks": [("Negro", 5), ("Blanco", 3)],
    },
    {
        "nombre": "Zapatilla Urbana Classic",
        "descripcion": "Diseno urbano con suela de goma",
        "precio": Decimal(74999),
        "marca": "Adidas",
        "categoria": "Urbano",
        "talle": "40",
        "imagen": "https://picsum.photos/seed/urbana-classic/600/600",
        "stocks": [("Blanco", 4)],
    },
    {
        "nombre": "Zapato Formal Cuero",
        "descripcion": "Cuero natural para ocasiones formales",
        "precio": Decimal(65999),
        "marca": "Bata",
        "categoria": "Formal",
        "talle": "41",
        "imagen": "https://picsum.photos/seed/formal-cuero/600/600",
        "stocks": [("Marron", 2)],
    },
    {
        "nombre": "Bota Trekking Andes",
        "descripcion": "Impermeable, para montana y senderismo",
        "precio": Decimal(129999),
        "marca": "Columbia",
        "categoria": "Outdoor",
        "talle": "43",
        "imagen": "https://picsum.photos/seed/trekking-andes/600/600",
        "stocks": [("Gris", 3)],
    },
    {
        "nombre": "Zapatilla Nino Sport",
        "descripcion": "Liviana y flexible para uso escolar",
        "precio": Decimal(39999),
        "marca": "Topper",
        "categoria": "Infantil",
        "talle": "32",
        "imagen": "https://picsum.photos/seed/nino-sport/600/600",
        "stocks": [("Azul", 6)],
    },
    {
        "nombre": "Sandalia Verano",
        "descripcion": "Sandalia liviana para playa y pileta",
        "precio": Decimal(24999),
        "marca": "Havaianas",
        "categoria": "Verano",
        "talle": "38",
        "imagen": "https://picsum.photos/seed/sandalia-verano/600/600",
        "stocks": [("Negro", 8)],
    },
]


def seed_admin() -> bool:
    """Create the admin gerente if it does not exist yet."""
    with get_session() as session:
        existente = session.exec(
            select(Gerente).where(Gerente.email == ADMIN_EMAIL)
        ).first()
        if existente:
            print(f"[skip] admin ya existe: {ADMIN_EMAIL}")
            return False

        session.add(
            Gerente(
                nombre=ADMIN_NOMBRE,
                email=ADMIN_EMAIL,
                contrasenia=hash_password(ADMIN_PASSWORD),
                telefono=ADMIN_TELEFONO,
            )
        )
        session.commit()
        print(f"[ok]   admin creado: {ADMIN_EMAIL}")
        return True


def seed_productos() -> int:
    """Create demo products (with stock) if they do not exist yet."""
    creados = 0
    with get_session() as session:
        for data in PRODUCTOS:
            existente = session.exec(
                select(Producto).where(
                    Producto.nombre == data["nombre"],
                    Producto.marca == data["marca"],
                )
            ).first()
            if existente:
                print(f"[skip] producto ya existe: {data['nombre']}")
                continue

            producto = Producto(
                nombre=data["nombre"],
                descripcion=data["descripcion"],
                precio=data["precio"],
                marca=data["marca"],
                categoria=data["categoria"],
                talle=data["talle"],
                imagen=data["imagen"],
            )
            session.add(producto)
            session.commit()
            session.refresh(producto)

            for color, cantidad in data["stocks"]:
                session.add(
                    Stocks(
                        producto_id=producto.id,
                        color=color,
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
    creados = seed_productos()
    print("--------------------")
    print(f"Productos nuevos: {creados}")
    print(f"Admin: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
    print("Login admin: http://localhost:3000/admin_login")


if __name__ == "__main__":
    main()
