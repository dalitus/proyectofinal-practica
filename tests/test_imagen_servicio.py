"""Tests de la imagen del producto (T-050, D-015, D-049).

La validacion corre en el servidor y el archivo se guarda con un nombre unico:
dos productos con una imagen llamada ``foto.png`` no pueden pisarse.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.service import imagen_servicio
from app.service.imagen_servicio import ErrorDeImagen

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 32


def test_guardar_escribe_con_nombre_unico(tmp_path: Path) -> None:
    primera = imagen_servicio.guardar("foto.PNG", PNG, tmp_path)
    segunda = imagen_servicio.guardar("foto.png", PNG, tmp_path)

    assert primera.startswith("/_upload/")
    assert primera.endswith(".png")
    assert primera != segunda
    assert (tmp_path / Path(primera).name).read_bytes() == PNG
    assert len(list(tmp_path.iterdir())) == 2


@pytest.mark.parametrize("nombre", ["foto.gif", "foto.pdf", "foto", "foto.jpg.exe"])
def test_rechaza_extensiones_que_no_son_imagen(tmp_path: Path, nombre: str) -> None:
    with pytest.raises(ErrorDeImagen) as error:
        imagen_servicio.guardar(nombre, PNG, tmp_path)

    assert error.value.args[0] == imagen_servicio.MENSAJE_DE_TIPO
    assert list(tmp_path.iterdir()) == []


def test_rechaza_archivos_de_mas_de_dos_megas(tmp_path: Path) -> None:
    grande = PNG + b"0" * imagen_servicio.TAMANO_MAXIMO

    with pytest.raises(ErrorDeImagen) as error:
        imagen_servicio.guardar("foto.webp", grande, tmp_path)

    assert error.value.args[0] == imagen_servicio.MENSAJE_DE_TAMANO
    assert list(tmp_path.iterdir()) == []


def test_rechaza_un_archivo_vacio(tmp_path: Path) -> None:
    with pytest.raises(ErrorDeImagen) as error:
        imagen_servicio.guardar("foto.jpg", b"", tmp_path)

    assert error.value.args[0] == imagen_servicio.MENSAJE_DE_ARCHIVO_VACIO


def test_borrar_ignora_las_imagenes_externas(tmp_path: Path) -> None:
    url = imagen_servicio.guardar("foto.png", PNG, tmp_path)

    assert imagen_servicio.borrar("https://picsum.photos/seed/x/600/600", tmp_path) is False
    assert imagen_servicio.borrar(url, tmp_path) is True
    assert list(tmp_path.iterdir()) == []
    assert imagen_servicio.borrar(url, tmp_path) is False
