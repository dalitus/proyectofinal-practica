from proyectofinal.state.catalogo_state import CatalogoState
s = CatalogoState()
s.cargar_productos()
print('Productos cargados:', len(s.productos))
for p in s.productos[:20]:
    print(p.get('id_producto'), p.get('nombre'), 'cantidad=', p.get('cantidad'))
