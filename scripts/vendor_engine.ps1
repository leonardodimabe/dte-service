# Vendoriza el motor dte_chile en .\vendor\dte_chile para el build de Docker.
# Uso: .\scripts\vendor_engine.ps1 [-Src ..\dte_chile]
param([string]$Src = "..\dte_chile")

if (-not (Test-Path "$Src\pyproject.toml")) {
    Write-Error "No encuentro el motor en '$Src' (falta pyproject.toml)."
    exit 1
}

$dest = "vendor\dte_chile"
if (Test-Path $dest) { Remove-Item -Recurse -Force $dest }
New-Item -ItemType Directory -Force -Path $dest | Out-Null

Copy-Item "$Src\pyproject.toml" $dest
Copy-Item "$Src\src" $dest -Recurse
if (Test-Path "$Src\README.md") { Copy-Item "$Src\README.md" $dest }

Write-Host "Motor vendorizado en $dest"
