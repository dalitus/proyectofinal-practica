"""Script para agregar columna direccion a users"""
from proyectofinal.repository.conect_db import engine
from sqlalchemy import text

try:
    with engine.connect() as connection:
        # Verificar si la columna existe
        result = connection.execute(
            text("SHOW COLUMNS FROM users LIKE 'direccion'")
        )
        if not result.fetchone():
            # Agregar columna si no existe
            connection.execute(
                text("ALTER TABLE users ADD COLUMN direccion VARCHAR(255) DEFAULT ''")
            )
            connection.commit()
            print("✅ Columna 'direccion' agregada exitosamente a users")
        else:
            print("✅ Columna 'direccion' ya existe en users")
except Exception as e:
    print(f"❌ Error: {e}")
