"""Log estructurado de las operaciones sensibles (T-053, D-031).

Hay una sola forma de dejar rastro: una línea JSON en el logger ``app.auditoria``
con quién, qué, sobre qué entidad y cuándo. No hay tabla ni pantalla de auditoría
(D-031), así que el log es la fuente: se escribe para que lo pueda leer una
persona y también un filtro.

Se llama desde el servicio, después de que la operación se confirmó: si la base
rechaza el cambio, no hay nada que auditar.

``configurar_destino`` agrega el archivo. Reflex no configura el logging de la
aplicación, así que un ``logger.info`` sin handler no llega a ningún lado: la
línea existiría en el código y se perdería al ejecutar. El destino se arma una
sola vez desde ``app/app.py``; los tests lo dejan sin tocar y leen con ``caplog``.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("app.auditoria")

RUTA_POR_DEFECTO = Path(__file__).resolve().parents[2] / "logs" / "auditoria.log"


def configurar_destino(ruta: Path | None = None) -> Path:
    """Append the audit lines to a file and return its path.

    Idempotente: llamarla dos veces no duplica las líneas.
    """
    destino = (ruta or RUTA_POR_DEFECTO).resolve()
    destino.parent.mkdir(parents=True, exist_ok=True)

    ya_configurado = any(
        isinstance(handler, logging.FileHandler)
        and Path(handler.baseFilename).resolve() == destino
        for handler in logger.handlers
    )
    if not ya_configurado:
        archivo = logging.FileHandler(destino, encoding="utf-8")
        # El mensaje ya es el JSON completo: fecha, autor, acción y entidad.
        archivo.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(archivo)

    logger.setLevel(logging.INFO)
    # La línea también sigue el camino normal: el log de la consola la muestra
    # y los tests la capturan sin conocer este archivo.
    logger.propagate = True
    return destino


def registrar(
    *,
    accion: str,
    entidad: str,
    entidad_id: int,
    admin_id: int | None = None,
    detalle: str = "",
) -> None:
    """Write one audit line.

    ``admin_id`` puede ser ``None`` mientras el panel no tenga la guarda de rol
    (T-023): es preferible una línea sin autor a ninguna línea.
    """
    logger.info(
        json.dumps(
            {
                "fecha": datetime.now().isoformat(timespec="seconds"),
                "admin_id": admin_id,
                "accion": accion,
                "entidad": entidad,
                "entidad_id": entidad_id,
                "detalle": detalle,
            },
            ensure_ascii=False,
        )
    )
