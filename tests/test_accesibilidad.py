"""Accesibilidad y responsive basico, verificados sobre el AST (T-074).

No mide contraste ni renderiza la pagina; corta las regresiones que ya
aparecieron una vez: inputs sin label, imagenes sin ``alt``, anchos fijos que
rompen 360px y spinners de pagina completa (D-034, docs/design.md 7).
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1] / "app"
PAGINAS = sorted((APP / "pages").glob("*.py"))

CAMPOS = {"Input", "Select", "TextArea"}
IMAGENES = {"image", "img"}
ANCHO_FIJO = re.compile(r"^\d{3,}(?:\.\d+)?px$")


def _arbol(ruta: Path) -> ast.Module:
    return ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))


def _llamadas(arbol: ast.Module):
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Call):
            yield nodo


def _nombre_llamada(nodo: ast.Call) -> str:
    if isinstance(nodo.func, ast.Name):
        return nodo.func.id
    if isinstance(nodo.func, ast.Attribute):
        return nodo.func.attr
    return ""


@pytest.mark.parametrize("ruta", PAGINAS, ids=lambda ruta: ruta.name)
def test_los_campos_tienen_label_visible(ruta: Path) -> None:
    """Todo input/select del sistema de diseno lleva label (design.md 7)."""
    sin_label = [
        f"{ruta.name}:{nodo.lineno}"
        for nodo in _llamadas(_arbol(ruta))
        if _nombre_llamada(nodo) in CAMPOS
        and not any(palabra.arg == "label" for palabra in nodo.keywords)
    ]

    assert sin_label == [], f"campos sin label: {sin_label}"


@pytest.mark.parametrize("ruta", PAGINAS, ids=lambda ruta: ruta.name)
def test_las_imagenes_tienen_alt(ruta: Path) -> None:
    """Toda imagen tiene ``alt``; las decorativas lo declaran vacio (design.md 7)."""
    sin_alt = [
        f"{ruta.name}:{nodo.lineno}"
        for nodo in _llamadas(_arbol(ruta))
        if _nombre_llamada(nodo) in IMAGENES
        and not any(palabra.arg == "alt" for palabra in nodo.keywords)
    ]

    assert sin_alt == [], f"imagenes sin alt: {sin_alt}"


@pytest.mark.parametrize("ruta", PAGINAS, ids=lambda ruta: ruta.name)
def test_sin_anchos_fijos_que_rompen_360(ruta: Path) -> None:
    """El layout es mobile-first: sin anchos en px que no entren en 360 (D-034)."""
    fijos = [
        f"{ruta.name}:{nodo.lineno} {nodo.arg}={nodo.value.value!r}"
        for nodo in ast.walk(_arbol(ruta))
        if isinstance(nodo, ast.keyword)
        and nodo.arg in {"width", "min_width", "max_width"}
        and isinstance(nodo.value, ast.Constant)
        and isinstance(nodo.value.value, str)
        and ANCHO_FIJO.match(nodo.value.value)
        and int(float(nodo.value.value.removesuffix("px"))) > 320
    ]

    assert fijos == [], f"anchos fijos en paginas: {fijos}"


def test_sin_spinner_de_pagina_completa() -> None:
    """La carga se comunica con Skeleton, no con un spinner global (design.md 8)."""
    culpables = [
        ruta.name
        for ruta in PAGINAS
        if any(_nombre_llamada(nodo) == "spinner" for nodo in _llamadas(_arbol(ruta)))
    ]

    assert culpables == []
