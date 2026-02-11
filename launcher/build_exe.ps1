$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$launcherDir = Join-Path $root "launcher"
$distDir = Join-Path $root "dist"
$buildDir = Join-Path $root "build"

Write-Host "Installing PyInstaller..."
python -m pip install --upgrade pip
python -m pip install pyinstaller

Write-Host "Building EXE..."
Set-Location $launcherDir
pyinstaller --onefile --name PakBankDiscountsLauncher `
  --distpath "$distDir" `
  --workpath "$buildDir" `
  --specpath "$launcherDir" `
  launcher.py

Write-Host "EXE created at $distDir\PakBankDiscountsLauncher.exe"
