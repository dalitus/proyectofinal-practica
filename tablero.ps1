<#
    Levanta el tablero kanban del backlog leyendo docs/backlog/*.md en vivo.

    Uso:
        .\tablero.ps1                 # solo lectura
        .\tablero.ps1 -Write          # permite arrastrar tarjetas y reescribir el .md
        .\tablero.ps1 -Port 9000
        .\tablero.ps1 -Open           # abre el navegador por defecto

    El tablero no genera archivos: sirve el HTML desde tools/tablero_backlog.py y
    empuja los cambios por SSE cuando cambia un .md. El markdown sigue siendo la
    fuente de verdad.
#>
param(
    [switch]$Write,
    [switch]$Open,
    [int]$Port = 8765
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

# Mismo criterio que run.ps1: el entorno oficial es .venv (D-027); se acepta
# venv solo como respaldo de instalaciones viejas.
$venvDir = @(".venv", "venv") |
    Where-Object { Test-Path (Join-Path $PSScriptRoot "$_\Scripts\python.exe") } |
    Select-Object -First 1
$python = if ($venvDir) {
    Join-Path $PSScriptRoot "$venvDir\Scripts\python.exe"
} else {
    "python"
}

$pythonArgs = @("tools\tablero_backlog.py", "--port", "$Port")
if ($Write) { $pythonArgs += "--write" }
if ($Open) { $pythonArgs += "--open" }

& $python @pythonArgs
