# ARIA Setup Script (Windows PowerShell)
# Run this once on a new machine to install all dependencies.

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent

Write-Host ""
Write-Host "+--------------------------------------+" -ForegroundColor Cyan
Write-Host "|      ARIA - Setup Script             |" -ForegroundColor Cyan
Write-Host "+--------------------------------------+" -ForegroundColor Cyan
Write-Host ""

#-------------------------------------------------------------------------------
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python 3.11+ is required. Install from https://python.org"
}

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Error "Node.js 20+ is required. Install from https://nodejs.org"
}

Write-Host "  OK Python: $(python --version)" -ForegroundColor Green
Write-Host "  OK Node:   $(node --version)" -ForegroundColor Green

#-------------------------------------------------------------------------------
Write-Host ""
Write-Host "Setting up Python virtual environment..." -ForegroundColor Yellow

$BackendDir = Join-Path $Root "backend"
$VenvDir = Join-Path $BackendDir "venv"

if (-not (Test-Path $VenvDir)) {
    python -m venv $VenvDir
    Write-Host "  OK Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "  OK Virtual environment already exists" -ForegroundColor Green
}

$PipPath = Join-Path $VenvDir "Scripts\pip.exe"
& $PipPath install --upgrade pip --quiet
& $PipPath install -r (Join-Path $BackendDir "requirements.txt") --quiet
Write-Host "  OK Python packages installed" -ForegroundColor Green

#-------------------------------------------------------------------------------
Write-Host ""
Write-Host "Installing Playwright browser (Chromium)..." -ForegroundColor Yellow

$PlaywrightPath = Join-Path $VenvDir "Scripts\playwright.exe"
& $PlaywrightPath install chromium
Write-Host "  OK Chromium installed" -ForegroundColor Green

#-------------------------------------------------------------------------------
Write-Host ""
Write-Host "Installing Node dependencies..." -ForegroundColor Yellow

Set-Location (Join-Path $Root "electron")
npm install --silent
Write-Host "  OK Electron dependencies installed" -ForegroundColor Green

Set-Location (Join-Path $Root "frontend")
npm install --silent
Write-Host "  OK Frontend dependencies installed" -ForegroundColor Green

#-------------------------------------------------------------------------------
Write-Host ""
Write-Host "Setting up environment config..." -ForegroundColor Yellow

$EnvExample = Join-Path $Root ".env.example"
$EnvFile = Join-Path $Root ".env"

if (-not (Test-Path $EnvFile)) {
    Copy-Item $EnvExample $EnvFile
    Write-Host "  OK .env created from .env.example" -ForegroundColor Green
    Write-Host "  WARN Edit .env and add your ANTHROPIC_API_KEY" -ForegroundColor Yellow
} else {
    Write-Host "  OK .env already exists" -ForegroundColor Green
}

# Also copy .env to backend dir for local loading
Copy-Item $EnvFile (Join-Path $BackendDir ".env") -Force

#-------------------------------------------------------------------------------
Write-Host ""
Write-Host "Creating ARIA output directory..." -ForegroundColor Yellow

$OutputDir = Join-Path $env:USERPROFILE "ARIA\outputs"
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
Write-Host "  OK Output directory: $OutputDir" -ForegroundColor Green

#-------------------------------------------------------------------------------
Write-Host ""
Write-Host "+--------------------------------------+" -ForegroundColor Green
Write-Host "|           Setup Complete!            |" -ForegroundColor Green
Write-Host "+--------------------------------------+" -ForegroundColor Green
Write-Host "|                                      |" -ForegroundColor Green
Write-Host "|  1. Edit .env -> add KEYS            |" -ForegroundColor Green
Write-Host "|  2. Run: .\scripts\start-dev.ps1      |" -ForegroundColor Green
Write-Host "|                                      |" -ForegroundColor Green
Write-Host "+--------------------------------------+" -ForegroundColor Green
Write-Host ""
