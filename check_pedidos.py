import pymysql
import json

conn = pymysql.connect(
    host='localhost',
    user='root',
    password='Dalecolon123',
    database='zapateria_db'
)
cursor = conn.cursor()

# Ver los últimos 3 pedidos
cursor.execute('SELECT id_pedido, id_users, total, productos_json FROM pedidos ORDER BY id_pedido DESC LIMIT 3')
resultados = cursor.fetchall()

for r in resultados:
    productos = r[3]
    if productos:
        print(f"Pedido #{r[0]}: usuario={r[1]}, total={r[2]}")
        print(f"  productos_json: {productos[:150]}")
    else:
        print(f"Pedido #{r[0]}: usuario={r[1]}, total={r[2]}, productos_json=NULL")

cursor.close()
conn.close()
