"""Tests de la configuracion de logging (T-064, D-035).

D-035 dejo una sola decision: stdout, sin archivo, con DEBUG en dev e INFO en
produccion. Estos tests fijan el nivel por entorno y que el handler no se
duplique cuando Reflex importa la app varias veces.
"""

from __future__ import annotations

import logging

import pytest

from app.service.configuracion_logs import FORMATO, configurar_logs, nivel_de_log


def test_nivel_por_entorno(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REFLEX_ENV_MODE", "dev")
    assert nivel_de_log() == logging.DEBUG

    monkeypatch.setenv("REFLEX_ENV_MODE", "prod")
    assert nivel_de_log() == logging.INFO

    # Preview no es desarrollo: se comporta como produccion.
    monkeypatch.setenv("REFLEX_ENV_MODE", "preview")
    assert nivel_de_log() == logging.INFO


def test_sin_variable_de_entorno_usa_dev(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("REFLEX_ENV_MODE", raising=False)

    assert nivel_de_log() == logging.DEBUG


def test_configurar_logs_usa_stdout_sin_duplicar(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("REFLEX_ENV_MODE", "dev")
    logger = logging.getLogger("app")
    nivel_anterior = logger.level
    antes = list(logger.handlers)

    try:
        configurar_logs()
        # Reflex importa la app mas de una vez: el handler no se duplica.
        configurar_logs()

        propios = [handler for handler in logger.handlers if handler not in antes]
        assert len(propios) == 1
        assert isinstance(propios[0], logging.StreamHandler)
        assert propios[0].formatter is not None
        assert propios[0].formatter._fmt == FORMATO
        assert logger.level == logging.DEBUG

        logging.getLogger("app.prueba").info("hola")
        salida = capsys.readouterr().out
    finally:
        for handler in list(logger.handlers):
            if handler not in antes:
                logger.removeHandler(handler)
                handler.close()
        logger.setLevel(nivel_anterior)

    assert "INFO app.prueba: hola" in salida
