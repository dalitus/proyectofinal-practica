"""Configuracion de logging de la aplicacion (T-064, D-035).

Reflex configura solo sus propios loggers: un ``logger.info`` de la app no llega
a ningun lado sin un handler. Este modulo arma el unico destino que decidio
D-035: stdout, sin archivo ni servicio externo, con nivel por entorno (``DEBUG``
en dev e ``INFO`` en produccion).

Se llama una sola vez desde ``app/app.py``; es idempotente porque Reflex importa
el modulo mas de una vez al compilar y al levantar el backend.
"""

from __future__ import annotations

import logging
import os
import sys

# Todos los loggers de la app empiezan con este prefijo: el handler se cuelga
# una sola vez del padre y los hijos propagan hasta aca.
NOMBRE_LOGGER = "app"

FORMATO = "%(asctime)s %(levelname)s %(name)s: %(message)s"

# Reflex publica el modo con el que se lanzo la CLI en esta variable.
VARIABLE_ENTORNO = "REFLEX_ENV_MODE"
MODO_POR_DEFECTO = "dev"

# Marca propia para reconocer el handler entre recargas sin duplicarlo.
_MARCA = "_handler_de_la_app"


def nivel_de_log(modo: str | None = None) -> int:
    """Return ``DEBUG`` in development and ``INFO`` anywhere else (D-035)."""
    actual = (modo or os.getenv(VARIABLE_ENTORNO, MODO_POR_DEFECTO)).strip().lower()
    return logging.DEBUG if actual == "dev" else logging.INFO


def configurar_logs() -> logging.Logger:
    """Send the application logs to stdout and return their parent logger.

    A ``StreamHandler`` on ``app`` covers every module (``app.auditoria``,
    ``app.state.*``, etc.). Reconfiguring updates the level, so a reload with a
    different ``REFLEX_ENV_MODE`` takes effect without restarting the process.
    """
    logger = logging.getLogger(NOMBRE_LOGGER)
    logger.setLevel(nivel_de_log())

    handler = next(
        (item for item in logger.handlers if getattr(item, _MARCA, False)),
        None,
    )
    if handler is None:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(FORMATO))
        setattr(handler, _MARCA, True)
        logger.addHandler(handler)
    else:
        # En tests o recargas sys.stdout puede ser otro objeto.
        handler.stream = sys.stdout

    return logger
