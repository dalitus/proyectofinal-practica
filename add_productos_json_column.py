import pymysql
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

# Obtener credenciales de la base de datos
db_host = "localhost"
db_user = "root"
db_password = "Dalecolon123"
db_name = "zapateria_db"

try:
    # Conectar a MySQL
    conn = pymysql.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name
    )
    cursor = conn.cursor()
    
    # Verificar si la columna existe
    cursor.execute("""
        SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME='pedidos' AND TABLE_SCHEMA='zapateria_db'
    """)
    columns = [col[0] for col in cursor.fetchall()]
    
    if 'productos_json' not in columns:
        # Agregar la columna
        cursor.execute("""
            ALTER TABLE pedidos ADD COLUMN productos_json LONGTEXT
        """)
        conn.commit()
        print("✅ Columna 'productos_json' agregada exitosamente a pedidos")
    else:
        print("ℹ️ Columna 'productos_json' ya existe en pedidos")
        
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
