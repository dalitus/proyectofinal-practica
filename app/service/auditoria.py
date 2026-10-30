"""Log estructurado de las operaciones sensibles (T-053, D-031).

Hay una sola forma de dejar rastro: una línea JSON en el logger ``app.auditoria``
con quién, qué, sobre qué entidad y cuándo. No hay tabla ni pantalla de auditoría
(D-031), así que el log es la fuente: se escribe para que lo pueda leer una
persona y también un filtro.

Se llama desde el servicio, después de que la operación se confirmó: si la base
rechaza el cambio, no hay nada que auditar.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime

logger = logging.getLogger("app.auditoria")


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
