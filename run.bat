@echo off
REM Levanta la app Reflex usando el entorno virtual del proyecto.
REM Uso: run.bat            (desarrollo)
REM      run.bat --env prod (produccion)
setlocal
cd /d "%~dp0"

if not exist "venv\Scripts\activate.bat" (
    echo No se encontro el entorno virtual en 'venv'.
    echo Crealo con: python -m venv venv ^&^& venv\Scripts\activate.bat ^&^& pip install -r requirements.txt
    exit /b 1
)

call "venv\Scripts\activate.bat"
reflex run %*
