"""Lectura de la ruta actual sin ``router.page`` (deprecado en Reflex 0.8.1).

El router de backend entrega ``router.url`` como un ``ReflexURL``: un ``str``
con ``path`` y ``query_parameters`` ya parseados. Eso alcanza para las rutas de
esta app (``/producto/[producto_id]``, ``/admin/pedidos/[pedido_id]``) y para
``?next=``, y evita el aviso de deprecacion de ``router.page.params``.

Un valor invalido no rompe la pagina: devuelve ``None`` o el valor por defecto,
y la pagina muestra su estado de "no existe" o su destino de siempre.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import parse_qsl


def _ruta(url: Any) -> str:
    """Path of the browser URL, whether the router hands a dict or an object."""
    if isinstance(url, dict):
        ruta = url.get("path", "")
    else:
        ruta = getattr(url, "path", "")
    return str(ruta or "")


def _consulta(url: Any) -> dict[str, str]:
    """Query-string values of the browser URL as a plain dict."""
    if isinstance(url, dict):
        valores = url.get("query_parameters")
        texto = url.get("query", "")
    else:
        valores = getattr(url, "query_parameters", None)
        texto = getattr(url, "query", "")

    if valores:
        return {str(clave): str(valor) for clave, valor in dict(valores).items()}
    return dict(parse_qsl(str(texto or "")))


def id_de_la_url(url: Any) -> int | None:
    """Turn the last path segment into an id (``/admin/pedidos/12`` -> ``12``)."""
    partes = [parte for parte in _ruta(url).split("/") if parte]
    if not partes:
        return None
    try:
        return int(partes[-1])
    except ValueError:
        return None


def valor_de_consulta(url: Any, nombre: str, por_defecto: str = "") -> str:
    """One query-string value, without the deprecation of ``router.page``."""
    return _consulta(url).get(nombre, por_defecto)


def ruta_interna(url: Any, por_defecto: str) -> str:
    """The current path when it is internal, else ``por_defecto``.

    An absolute URL or ``//host`` would turn ``?next=`` into an open redirect.
    """
    ruta = _ruta(url)
    if not ruta.startswith("/") or ruta.startswith("//"):
        return por_defecto
    return ruta
