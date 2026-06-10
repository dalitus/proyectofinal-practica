from sqlmodel import Session, select
from proyectofinal.model.consulta_model import Consulta
from proyectofinal.repository.conect_db import engine
from datetime import datetime

# Crear consulta
def crear_consulta_repo(usuario_id: int, asunto: str, mensaje: str):
    consulta = Consulta(
        usuario_id=usuario_id,   # 👈 corregido
        asunto=asunto,
        mensaje=mensaje,
        respuesta=None,
        fecha=datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # opcional si tu modelo tiene fecha
    )
    with Session(engine) as session:
        session.add(consulta)
        session.commit()
        session.refresh(consulta)
    return consulta

# Listar consultas por usuario
def listar_consultas_usuario_repo(usuario_id: int):
    with Session(engine) as session:
        statement = select(Consulta).where(Consulta.usuario_id == usuario_id)   # 👈 corregido
        results = session.exec(statement)
        return results.all()

# Responder consulta
def responder_consulta_repo(consulta_id: int, respuesta: str):
    with Session(engine) as session:
        consulta = session.get(Consulta, consulta_id)
        if consulta:
            consulta.respuesta = respuesta
            session.add(consulta)
            session.commit()
            session.refresh(consulta)
            return consulta
    return None

# Alias para el servicio
def listar_consultas_usuario(usuario_id: int):
    return listar_consultas_usuario_repo(usuario_id)

# Listar todas las consultas
def listar_todas_consultas_repo():
    with Session(engine) as session:
        statement = select(Consulta)
        results = session.exec(statement)
        return results.all()
    
# Eliminar consulta
def eliminar_consulta_repo(consulta_id: int):
    with Session(engine) as session:
        consulta = session.get(Consulta, consulta_id)
        if consulta:
            session.delete(consulta)
            session.commit()