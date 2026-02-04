from proyectofinal.service.catalogo_service import obtener_catalogo

productos = obtener_catalogo()
print('Productos cargados:', len(productos))
for p in productos[:50]:
    print(p.get('id_producto'), p.get('nombre'), 'cantidad=', p.get('cantidad'))
