from app.repository.consulta_repocitory import (
    crear_consulta_repo,
    listar_consultas_usuario_repo,
    responder_consulta_repo,
    eliminar_consulta_repo,
    listar_todas_consultas_repo,
)


def crear_consulta(id_users: int, asunto: str, mensaje: str):
    if not id_users or not asunto or not mensaje:
        raise ValueError("Todos los campos son obligatorios")
    return crear_consulta_repo(id_users, asunto, mensaje)


def listar_consultas_usuario(id_users: int):
    return listar_consultas_usuario_repo(id_users)


def listar_todas_consultas():
    return listar_todas_consultas_repo()


def responder_consulta(consulta_id: int, respuesta: str):
    consulta = responder_consulta_repo(consulta_id, respuesta)
    if not consulta:
        raise ValueError(f"No se encontró la consulta con ID {consulta_id}")
    return consulta


def eliminar_consulta(consulta_id: int):
    eliminar_consulta_repo(consulta_id)