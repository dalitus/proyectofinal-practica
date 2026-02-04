from proyectofinal.service.consulta_service import listar_todas_consultas

c = listar_todas_consultas()
print(f"Total consultas: {len(c)}")
for x in c:
    print(x.id_consulta, x.asunto)
