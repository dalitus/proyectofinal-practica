"""Validacion y guardado de la imagen de un producto (D-015, D-049).

El navegador elige el archivo con ``rx.upload``; este modulo decide si sirve y
donde queda. La validacion corre en el servidor: el ``accept`` del componente es
una ayuda para la persona, no un permiso.

Reflex 0.10.1 guarda las subidas en ``uploaded_files/`` (``rx.get_upload_dir``)
y las sirve en ``/_upload/<archivo>``. El nombre unico evita pisar la imagen de
otro producto y la DB guarda esa ruta relativa, no el archivo.
"""

from __future__ import annotations

import uuid
from pathlib import Path

# Sufijo -> tipo MIME. Es la lista blanca de D-015.
TIPOS_PERMITIDOS: dict[str, str] = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}

TAMANO_MAXIMO = 2 * 1024 * 1024

MENSAJE_DE_TIPO = "La imagen tiene que ser JPG, PNG o WebP."
MENSAJE_DE_TAMANO = "La imagen no puede superar los 2 MB."
MENSAJE_DE_ARCHIVO_VACIO = "El archivo esta vacio."
MENSAJE_SIN_ARCHIVO = "Elegi un archivo antes de subirlo."

PREFIJO_PUBLICO = "/_upload/"


class ErrorDeImagen(ValueError):
    """The file is not an image the app accepts; the message is user-facing."""


def validar(nombre: str, tamano: int) -> str:
    """Return the normalised extension or raise ``ErrorDeImagen``."""
    sufijo = Path(nombre or "").suffix.lower()
    if sufijo not in TIPOS_PERMITIDOS:
        raise ErrorDeImagen(MENSAJE_DE_TIPO)
    if tamano <= 0:
        raise ErrorDeImagen(MENSAJE_DE_ARCHIVO_VACIO)
    if tamano > TAMANO_MAXIMO:
        raise ErrorDeImagen(MENSAJE_DE_TAMANO)
    return sufijo


def guardar(nombre: str, datos: bytes, directorio: Path) -> str:
    """Validate, save with a unique name and return the public URL.

    ``directorio`` se recibe y no se calcula aca para que los tests escriban en
    un directorio temporal y el estado decida cual es el de la aplicacion.
    """
    sufijo = validar(nombre, len(datos))
    directorio.mkdir(parents=True, exist_ok=True)

    archivo = f"{uuid.uuid4().hex}{sufijo}"
    (directorio / archivo).write_bytes(datos)
    return f"{PREFIJO_PUBLICO}{archivo}"


def borrar(url: str | None, directorio: Path) -> bool:
    """Delete a managed image, if ``url`` points at one.

    Las imagenes externas (las del seed, por ejemplo) no se tocan: el
    directorio solo contiene lo que subio el admin.
    """
    if not url or not url.startswith(PREFIJO_PUBLICO):
        return False

    archivo = directorio / Path(url.removeprefix(PREFIJO_PUBLICO)).name
    if not archivo.is_file():
        return False

    archivo.unlink()
    return True
