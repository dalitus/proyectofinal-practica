"""Tests del registro y del bootstrap del administrador (D-013, D-018, D-019).

Los servicios abren su propia sesion; `conftest.py` los apunta al engine de
`zapateria_test`. El parametro `session` se usa solo para verificar la base.
"""

from __future__ import annotations

import pytest
from reflex_local_auth import LocalUser
from sqlmodel import Session, select

from app.model import UserProfile
from app.service.auth_servicio import (
    ErrorDeRegistro,
    cambiar_password,
    crear_admin_si_no_existe,
    desactivar_usuario,
    normalizar_email,
    obtener_perfil,
    perfil_por_email,
    registrar_comprador,
)


def _contar(session: Session, model: type) -> int:
    return len(session.exec(select(model)).all())


def test_registro_crea_usuario_y_perfil(session: Session) -> None:
    perfil = registrar_comprador(
        email="Ana.Perez@Example.com",
        password="Clave-12345",
        nombre="Ana",
        apellido="Perez",
        telefono="3497657610",
    )

    usuario = session.exec(
        select(LocalUser).where(LocalUser.username == "ana.perez@example.com")
    ).one()
    assert usuario.enabled is True
    assert usuario.verify("Clave-12345") is True
    assert usuario.verify("otra-clave") is False

    assert perfil.local_user_id == usuario.id
    assert perfil.email == "ana.perez@example.com"
    assert perfil.nombre == "Ana"
    assert perfil.is_admin is False


def test_registro_no_expone_el_hash(session: Session) -> None:
    registrar_comprador(email="hash@example.com", password="Clave-12345")
    usuario = session.exec(
        select(LocalUser).where(LocalUser.username == "hash@example.com")
    ).one()

    assert "password_hash" not in usuario.model_dump()


def test_email_duplicado_no_deja_restos(session: Session) -> None:
    registrar_comprador(email="repetido@example.com", password="Clave-12345")

    with pytest.raises(ErrorDeRegistro):
        registrar_comprador(email="REPETIDO@example.com", password="Otra-Clave-1")

    assert _contar(session, LocalUser) == 1
    assert _contar(session, UserProfile) == 1


@pytest.mark.parametrize(
    ("email", "password"),
    [
        ("sin-arroba", "Clave-12345"),
        ("sin@dominio", "Clave-12345"),
        ("ok@example.com", "corta"),
        ("ok@example.com", ""),
    ],
)
def test_datos_invalidos_no_crean_nada(
    session: Session, email: str, password: str
) -> None:
    with pytest.raises(ErrorDeRegistro):
        registrar_comprador(email=email, password=password)

    assert _contar(session, LocalUser) == 0
    assert _contar(session, UserProfile) == 0


def test_normalizar_email_limpia_espacios_y_mayusculas() -> None:
    assert normalizar_email("  Cliente@Tienda.COM  ") == "cliente@tienda.com"

    with pytest.raises(ErrorDeRegistro):
        normalizar_email("no-es-un-email")


def test_admin_es_idempotente(session: Session) -> None:
    primero = crear_admin_si_no_existe(
        email="admin@zapateria.com", password="Secreta-123"
    )
    segundo = crear_admin_si_no_existe(
        email="admin@zapateria.com", password="Secreta-123"
    )

    assert primero is True
    assert segundo is False
    assert _contar(session, LocalUser) == 1

    perfil = perfil_por_email("admin@zapateria.com")
    assert perfil is not None
    assert perfil.is_admin is True

    usuario = session.exec(
        select(LocalUser).where(LocalUser.username == "admin@zapateria.com")
    ).one()
    assert usuario.verify("Secreta-123") is True


def test_obtener_perfil_por_id_de_usuario() -> None:
    perfil = registrar_comprador(email="buscar@example.com", password="Clave-12345")

    encontrado = obtener_perfil(perfil.local_user_id)
    assert encontrado is not None
    assert encontrado.email == "buscar@example.com"
    assert obtener_perfil(999999) is None


def test_cambiar_password_actualiza_hash_con_la_contrasena_nueva(
    session: Session,
) -> None:
    perfil = registrar_comprador(email="clave@example.com", password="Clave-12345")

    cambiar_password(
        perfil.local_user_id,
        password_actual="Clave-12345",
        password_nueva="Clave-Nueva-999",
    )

    usuario = session.exec(
        select(LocalUser).where(LocalUser.id == perfil.local_user_id)
    ).one()
    assert usuario.verify("Clave-Nueva-999") is True
    assert usuario.verify("Clave-12345") is False

    with pytest.raises(ValueError, match="actual"):
        cambiar_password(
            perfil.local_user_id,
            password_actual="incorrecta",
            password_nueva="Otra-Clave-1",
        )


def test_ultimo_admin_no_se_puede_desactivar(session: Session) -> None:
    created = crear_admin_si_no_existe(
        email="admin1@zapateria.com", password="Secreta-123"
    )
    assert created is True
    admin1 = perfil_por_email("admin1@zapateria.com")
    assert admin1 is not None

    with pytest.raises(ValueError, match="último administrador"):
        desactivar_usuario(admin1.local_user_id)

    created_2 = crear_admin_si_no_existe(
        email="admin2@zapateria.com", password="Secreta-456"
    )
    assert created_2 is True
    admin2 = perfil_por_email("admin2@zapateria.com")
    assert admin2 is not None

    desactivar_usuario(admin2.local_user_id)

    usuario = session.exec(
        select(LocalUser).where(LocalUser.id == admin2.local_user_id)
    ).one()
    assert usuario.enabled is False
