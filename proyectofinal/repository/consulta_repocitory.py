# proyectofinal/repository/consulta_repo.py
from sqlmodel import Session, select
from proyectofinal.model.consulta_model import Consulta
from proyectofinal.repository.conect_db import engine
from datetime import datetime

# Crear consulta
def crear_consulta_repo(usuario_id: int, asunto: str, mensaje: str):
    consulta = Consulta(
        usuario_id=usuario_id,
        asunto=asunto,
        mensaje=mensaje,
        respuesta=None,
        fecha_creacion=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    with Session(engine) as session:
        session.add(consulta)
        session.commit()
        session.refresh(consulta)
    return consulta

# Listar consultas por usuario
def listar_consultas_usuario_repo(usuario_id: int):
    with Session(engine) as session:
        statement = select(Consulta).where(Consulta.usuario_id == usuario_id)
        results = session.exec(statement)
        return results.all()

# Responder consulta
def responder_consulta_repo(consulta_id: int, respuesta: str):
    with Session(engine) as session:
        consulta = session.get(Consulta, consulta_id)
        if consulta:
            consulta.respuesta = respuesta
            consulta.fecha_respuesta = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            session.add(consulta)
            session.commit()
            session.refresh(consulta)
            return consulta
    return None

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
