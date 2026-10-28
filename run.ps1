<#
    Levanta la app Reflex usando el entorno virtual del proyecto.

    Uso:
        .\run.ps1             # modo desarrollo (recarga automatica)
        .\run.ps1 -Prod       # modo produccion
        .\run.ps1 -Port 3001  # cambiar el puerto del frontend

    Es importante activar el venv: reflex lanza el servidor backend con el
    comando "granian" tomado del PATH. Si el venv no esta activo puede usar
    un granian/reflex instalado globalmente y el backend falla al arrancar.

    El entorno lo crea `uv sync` en `.venv` (D-027). Se acepta `venv` como
    alternativa para instalaciones viejas.
#>
param(
    [switch]$Prod,
    [int]$Port = 0
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

$venvDir = @(".venv", "venv") |
    Where-Object { Test-Path (Join-Path $PSScriptRoot "$_\Scripts\Activate.ps1") } |
    Select-Object -First 1

if (-not $venvDir) {
    Write-Host "No se encontro el entorno virtual (.venv/ o venv/)." -ForegroundColor Red
    Write-Host "Crealo con: uv sync"
    exit 1
}

$activate = Join-Path $PSScriptRoot "$venvDir\Scripts\Activate.ps1"
& $activate

$reflexArgs = @("run")
if ($Prod) { $reflexArgs += @("--env", "prod") }
if ($Port -gt 0) { $reflexArgs += @("--frontend-port", "$Port") }

Write-Host "Ejecutando: reflex $($reflexArgs -join ' ')" -ForegroundColor Cyan
& reflex @reflexArgs
