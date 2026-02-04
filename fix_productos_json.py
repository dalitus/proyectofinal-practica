import pymysql

db_host = "localhost"
db_user = "root"
db_password = "Dalecolon123"
db_name = "zapateria_db"

try:
    conn = pymysql.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name
    )
    cursor = conn.cursor()
    
    # Actualizar todos los productos_json NULL a array vacío
    cursor.execute("""
        UPDATE pedidos SET productos_json = '[]' WHERE productos_json IS NULL
    """)
    conn.commit()
    print(f"✅ {cursor.rowcount} pedidos actualizados")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
