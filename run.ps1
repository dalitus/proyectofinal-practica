<#
    Levanta la app Reflex usando el entorno virtual del proyecto.

    Uso:
        .\run.ps1             # modo desarrollo (recarga automatica)
        .\run.ps1 -Prod       # modo produccion
        .\run.ps1 -Port 3001  # cambiar el puerto del frontend

    Es importante activar el venv: reflex lanza el servidor backend con el
    comando "granian" tomado del PATH. Si el venv no esta activo puede usar
    un granian/reflex instalado globalmente y el backend falla al arrancar.
#>
param(
    [switch]$Prod,
    [int]$Port = 0
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

$activate = Join-Path $PSScriptRoot "venv\Scripts\Activate.ps1"
if (-not (Test-Path $activate)) {
    Write-Host "No se encontro el entorno virtual en 'venv'." -ForegroundColor Red
    Write-Host "Crealo con: python -m venv venv; .\venv\Scripts\Activate.ps1; pip install -r requirements.txt"
    exit 1
}

& $activate

$reflexArgs = @("run")
if ($Prod) { $reflexArgs += @("--env", "prod") }
if ($Port -gt 0) { $reflexArgs += @("--frontend-port", "$Port") }

Write-Host "Ejecutando: reflex $($reflexArgs -join ' ')" -ForegroundColor Cyan
& reflex @reflexArgs
