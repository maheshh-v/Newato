# ARIA Build Installer Script
# Automates the full process of building the frontend, preparing Electron, 
# and generating a Windows NSIS installer.

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent

Write-Host ""
Write-Host "+----------------------------------------------+" -ForegroundColor Cyan
Write-Host "|         ARIA - Build Installer Script        |" -ForegroundColor Cyan
Write-Host "|   Preparing application for distribution     |" -ForegroundColor Cyan
Write-Host "+----------------------------------------------+" -ForegroundColor Cyan
Write-Host ""

# [1/4] Build React Frontend
Write-Host "[1/4] Building React frontend..." -ForegroundColor Yellow
Set-Location (Join-Path $Root "frontend")
npm install
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "  FAIL Frontend build failed" -ForegroundColor Red
    exit 1
}
Write-Host "  OK Frontend built" -ForegroundColor Green

# [2/4] Sync with Electron
Write-Host ""
Write-Host "[2/4] Syncing frontend dist with Electron..." -ForegroundColor Yellow
$ElectronDist = Join-Path $Root "electron\dist"
if (Test-Path $ElectronDist) {
    Remove-Item -Recurse -Force $ElectronDist
}
New-Item -ItemType Directory -Path $ElectronDist | Out-Null
Copy-Item -Path (Join-Path $Root "frontend\dist\*") -Destination $ElectronDist -Recurse
Write-Host "  OK Frontend files synced to electron/dist" -ForegroundColor Green

# [3/4] Prepare Electron
Write-Host ""
Write-Host "[3/4] Preparing Electron..." -ForegroundColor Yellow
Set-Location (Join-Path $Root "electron")
npm install
Write-Host "  OK Electron dependencies ready" -ForegroundColor Green

# [4/4] Package Application
Write-Host ""
Write-Host "[4/4] Packaging application (NSIS)..." -ForegroundColor Yellow
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "  FAIL Packaging failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "+----------------------------------------------+" -ForegroundColor Green
Write-Host "|            Build Complete!                    |" -ForegroundColor Green
Write-Host "+----------------------------------------------+" -ForegroundColor Green
Write-Host "|                                              |" -ForegroundColor Green
Write-Host "|  Installer created in:                       |" -ForegroundColor Green
Write-Host "|  \dist-installer\ARIA Setup 1.0.0.exe        |" -ForegroundColor Cyan
Write-Host "|                                              |" -ForegroundColor Green
Write-Host "+----------------------------------------------+" -ForegroundColor Green
Write-Host ""

Set-Location $Root
