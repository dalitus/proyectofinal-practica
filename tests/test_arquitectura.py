"""Reglas de capas del proyecto, verificadas sobre el AST (T-062, T-063, T-064).

No reemplazan una revisión de código, pero cortan las regresiones que ya
pasaron una vez: estados que abren sesiones, páginas que consultan la base,
`print()` de depuración y estilos sueltos en las páginas.

El orden obligatorio es `repository → service → state → pages` (D-033): el
estado no conoce el engine y la página no conoce la base.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1] / "app"

PROHIBIDO_EN_ESTADOS = ("app.repository", "sqlmodel")
PROHIBIDO_EN_PAGINAS = ("app.repository",)

# Llamadas que abren una sesión o crean el engine.
LLAMADAS_DE_BASE = ("Session", "get_session", "create_engine", "get_db")

COLOR_SUELTO = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")


def _modulos(carpeta: str) -> list[Path]:
    return sorted((APP / carpeta).glob("*.py"))


def _arbol(ruta: Path) -> ast.Module:
    return ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))


def _imports(arbol: ast.Module) -> set[str]:
    nombres: set[str] = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            nombres.update(alias.name for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            nombres.add(nodo.module)
    return nombres


def _llamadas(arbol: ast.Module) -> set[str]:
    nombres: set[str] = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Call):
            if isinstance(nodo.func, ast.Name):
                nombres.add(nodo.func.id)
            elif isinstance(nodo.func, ast.Attribute):
                nombres.add(nodo.func.attr)
    return nombres


@pytest.mark.parametrize("ruta", _modulos("state"), ids=lambda ruta: ruta.name)
def test_los_estados_no_tocan_la_base(ruta: Path) -> None:
    """El estado llama services, nunca al repositorio ni a una sesión (D-033)."""
    arbol = _arbol(ruta)
    modulos = _imports(arbol)
    prohibidos = {
        modulo
        for modulo in modulos
        if any(modulo == p or modulo.startswith(f"{p}.") for p in PROHIBIDO_EN_ESTADOS)
    }

    assert prohibidos == set(), f"{ruta.name} importa {sorted(prohibidos)}"
    assert not (set(LLAMADAS_DE_BASE) & _llamadas(arbol)), (
        f"{ruta.name} abre una sesión en vez de llamar a un service"
    )


@pytest.mark.parametrize("ruta", _modulos("pages"), ids=lambda ruta: ruta.name)
def test_las_paginas_no_acceden_a_datos(ruta: Path) -> None:
    """La página compone; los datos llegan por el estado."""
    arbol = _arbol(ruta)
    modulos = _imports(arbol)
    prohibidos = {
        modulo
        for modulo in modulos
        if any(modulo == p or modulo.startswith(f"{p}.") for p in PROHIBIDO_EN_PAGINAS)
    }

    assert prohibidos == set(), f"{ruta.name} importa {sorted(prohibidos)}"
    assert not (set(LLAMADAS_DE_BASE) & _llamadas(arbol)), (
        f"{ruta.name} abre una sesión en vez de leer del estado"
    )


def test_las_pantallas_de_admin_declaran_su_propio_on_load() -> None:
    """El evento heredado corre sobre la clase base y pierde los datos (T-023).

    En Reflex un handler queda atado a la clase que lo define, asi que una
    subclase con solo ``_cargar`` nunca lo ejecuta. El test corta esa regresion.
    """
    faltantes: list[str] = []

    for ruta in _modulos("state"):
        for nodo in ast.walk(_arbol(ruta)):
            if not isinstance(nodo, ast.ClassDef) or nodo.name == "AdminEstado":
                continue
            bases = {ast.unparse(base) for base in nodo.bases}
            if "AdminEstado" not in bases:
                continue

            metodos = {
                hijo.name
                for hijo in nodo.body
                if isinstance(hijo, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
            for evento in ("on_load", "reintentar", "_cargar"):
                if evento not in metodos:
                    faltantes.append(f"{ruta.name}:{nodo.name}.{evento}")

    assert faltantes == []


def test_sin_print_de_depuracion() -> None:
    """Los errores van a `logging`, no a la consola (T-064)."""
    culpables = [
        ruta.relative_to(APP).as_posix()
        for ruta in APP.rglob("*.py")
        if "print" in _llamadas(_arbol(ruta))
    ]

    assert culpables == []


def test_sin_traceback_crudo_al_usuario() -> None:
    culpables = [
        ruta.relative_to(APP).as_posix()
        for ruta in APP.rglob("*.py")
        if {"traceback", "print_exc"} & (_imports(_arbol(ruta)) | _llamadas(_arbol(ruta)))
    ]

    assert culpables == []


@pytest.mark.parametrize("ruta", _modulos("pages"), ids=lambda ruta: ruta.name)
def test_las_paginas_usan_el_sistema_de_diseno(ruta: Path) -> None:
    """Sin hex sueltos, `box_shadow` ni `color_scheme` en páginas (T-063)."""
    arbol = _arbol(ruta)

    hexes = [
        nodo.value
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Constant)
        and isinstance(nodo.value, str)
        and COLOR_SUELTO.match(nodo.value)
    ]
    estilos = {
        palabra.arg
        for palabra in ast.walk(arbol)
        if isinstance(palabra, ast.keyword) and palabra.arg in {"box_shadow", "color_scheme"}
    }

    assert hexes == [], f"{ruta.name} usa colores literales {hexes}"
    assert estilos == set(), f"{ruta.name} usa {sorted(estilos)}"
