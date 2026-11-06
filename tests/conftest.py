"""Fixtures de pytest contra MySQL `zapateria_test` (D-036).

La URL de test se deriva de `DATABASE_URL` cambiando solo el nombre de la base,
salvo que exista `TEST_DATABASE_URL`. Los tests nunca tocan `zapateria_db`.
"""

from __future__ import annotations

import os

import pytest
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.engine import Engine, make_url
from sqlmodel import Session, SQLModel, create_engine

import app.model  # noqa: F401  (registra todas las tablas)

load_dotenv()


def _test_url() -> str:
    explicit = os.getenv("TEST_DATABASE_URL")
    if explicit:
        return explicit

    base = os.getenv("DATABASE_URL")
    if not base:
        pytest.exit("DATABASE_URL is not set; copy .env.example to .env", returncode=1)

    url = make_url(base).set(database="zapateria_test")
    return url.render_as_string(hide_password=False)


@pytest.fixture(scope="session")
def engine() -> Engine:
    """Engine de la base de test, con el esquema creado y limpio al final."""
    engine = create_engine(_test_url(), pool_pre_ping=True)
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def session(engine: Engine) -> Session:
    """Sesion limpia por test: vacia las tablas antes de empezar."""
    with engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        for table in reversed(SQLModel.metadata.sorted_tables):
            conn.execute(text(f"DELETE FROM `{table.name}`"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))

    with Session(engine) as session:
        yield session


@pytest.fixture(autouse=True)
def _engine_de_test(engine: Engine, monkeypatch: pytest.MonkeyPatch) -> None:
    """Point the app engine at the test database for every test.

    Services open their own sessions (D-033), so tests inject the test engine
    instead of passing sessions around. Nothing here can reach `zapateria_db`.
    """
    from app.repository import base_de_datos

    monkeypatch.setattr(base_de_datos, "engine", engine)
