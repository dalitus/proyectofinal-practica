from proyectofinal.service.consulta_service import listar_todas_consultas
c = [x.dict() for x in listar_todas_consultas()]
print('Antes de ordenar:')
for x in c:
    print(x['id_consulta'], 'respuesta=', bool(x.get('respuesta')))
# Simular la orden de cargar_consultas
c.sort(key=lambda x: bool(x.get('respuesta')))
print('\nDespués de ordenar:')
for x in c:
    print(x['id_consulta'], 'respuesta=', bool(x.get('respuesta')))
