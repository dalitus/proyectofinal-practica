"""Imagen de producto: de la ruta guardada a una URL que el navegador carga.

La base guarda dos clases de ``imagen``: una URL externa (las del seed) o la
ruta relativa de un archivo subido por el admin (``/_upload/<archivo>``, D-049).
El frontend no sirve esa carpeta —la monta el backend—, asi que la ruta relativa
se convierte con ``rx.get_upload_url``, que resuelve el origen correcto en
desarrollo y en produccion.

La conversion vive aca y no en cada pagina: si cambia la forma de servir las
subidas, se cambia en un solo lugar.
"""

from __future__ import annotations

from typing import Any

import reflex as rx

# Prefijo publico de las subidas de Reflex (`Endpoint.UPLOAD`).
PREFIJO_SUBIDAS = "/_upload/"


def src_de_imagen(valor: Any) -> Any:
    """Return the URL to render for a stored image value.

    A value that starts with ``/_upload/`` is an uploaded file and becomes an
    absolute URL to the backend; anything else (external URL, empty string) is
    returned untouched.
    """
    texto = rx.Var.create(valor).to(str)
    return rx.cond(
        texto.startswith(PREFIJO_SUBIDAS),
        rx.get_upload_url(texto[len(PREFIJO_SUBIDAS) :]),
        texto,
    )
