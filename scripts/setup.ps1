# ARIA Setup Script (Windows PowerShell)
# Run this once on a new machine to install all dependencies.
# Usage: .\scripts\setup.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent

Write-Host ""
Write-Host "+----------------------------------------------+" -ForegroundColor Cyan
Write-Host "|         ARIA - Setup Script                  |" -ForegroundColor Cyan
Write-Host "|   Autonomous Reasoning & Intelligence Agent  |" -ForegroundColor Cyan
Write-Host "+----------------------------------------------+" -ForegroundColor Cyan
Write-Host ""

# --- Prerequisites ------------------------------------------------------------

Write-Host "[1/7] Checking prerequisites..." -ForegroundColor Yellow

# Check Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "  FAIL Python not found!" -ForegroundColor Red
    Write-Host "       Install Python 3.11+ from https://python.org" -ForegroundColor Red
    exit 1
}
$pyVer = python --version 2>&1
$pyMatch = [regex]::Match($pyVer, '(\d+)\.(\d+)')
if ($pyMatch.Success) {
    $pyMajor = [int]$pyMatch.Groups[1].Value
    $pyMinor = [int]$pyMatch.Groups[2].Value
    if ($pyMajor -lt 3 -or ($pyMajor -eq 3 -and $pyMinor -lt 11)) {
        Write-Host "  FAIL Python 3.11+ required, found $pyVer" -ForegroundColor Red
        exit 1
    }
}
Write-Host "  OK Python: $pyVer" -ForegroundColor Green

# Check Node
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "  FAIL Node.js not found!" -ForegroundColor Red
    Write-Host "       Install Node.js 20+ from https://nodejs.org" -ForegroundColor Red
    exit 1
}
$nodeVer = node --version 2>&1
$nodeMatch = [regex]::Match($nodeVer, 'v?(\d+)')
if ($nodeMatch.Success) {
    $nodeMajor = [int]$nodeMatch.Groups[1].Value
    if ($nodeMajor -lt 20) {
        Write-Host "  FAIL Node.js 20+ required, found $nodeVer" -ForegroundColor Red
        exit 1
    }
}
Write-Host "  OK Node:   $nodeVer" -ForegroundColor Green

# --- Python Virtual Environment -----------------------------------------------

Write-Host ""
Write-Host "[2/7] Setting up Python virtual environment..." -ForegroundColor Yellow

$BackendDir = Join-Path $Root "backend"
$VenvDir = Join-Path $BackendDir "venv"

if (-not (Test-Path $VenvDir)) {
    python -m venv $VenvDir
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  FAIL Could not create virtual environment" -ForegroundColor Red
        exit 1
    }
    Write-Host "  OK Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "  OK Virtual environment already exists" -ForegroundColor Green
}

# --- Python Dependencies ------------------------------------------------------

Write-Host ""
Write-Host "[3/7] Installing Python packages..." -ForegroundColor Yellow

$PipPath = Join-Path $VenvDir "Scripts\pip.exe"
# We wrap pip calls to ignore stderr warnings that PowerShell 'Stop' preference misinterprets
try {
    & $PipPath install --upgrade pip --quiet *>$null
} catch {} 

& $PipPath install -r (Join-Path $BackendDir "requirements.txt") --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "  FAIL pip install failed - check requirements.txt" -ForegroundColor Red
    exit 1
}
Write-Host "  OK Python packages installed" -ForegroundColor Green

# --- Playwright Browser -------------------------------------------------------

Write-Host ""
Write-Host "[4/7] Installing Playwright browser (Chromium)..." -ForegroundColor Yellow

$PlaywrightPath = Join-Path $VenvDir "Scripts\playwright.exe"
if (Test-Path $PlaywrightPath) {
    try {
        & $PlaywrightPath install chromium *>$null
    } catch {}
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  WARN Playwright install had issues - browser automation may not work" -ForegroundColor Yellow
    } else {
        Write-Host "  OK Chromium installed" -ForegroundColor Green
    }
} else {
    Write-Host "  WARN playwright.exe not found - run 'pip install playwright' manually" -ForegroundColor Yellow
}

# --- Node Dependencies --------------------------------------------------------

Write-Host ""
Write-Host "[5/7] Installing Node dependencies..." -ForegroundColor Yellow

$ElectronDir = Join-Path $Root "electron"
$FrontendDir = Join-Path $Root "frontend"

Push-Location $ElectronDir
try { npm install --silent *>$null } catch {}
if ($LASTEXITCODE -ne 0) {
    Write-Host "  FAIL Electron npm install failed" -ForegroundColor Red
    Pop-Location
    exit 1
}
Pop-Location
Write-Host "  OK Electron dependencies installed" -ForegroundColor Green

Push-Location $FrontendDir
try { npm install --silent *>$null } catch {}
if ($LASTEXITCODE -ne 0) {
    Write-Host "  FAIL Frontend npm install failed" -ForegroundColor Red
    Pop-Location
    exit 1
}
Pop-Location
Write-Host "  OK Frontend dependencies installed" -ForegroundColor Green

# --- Environment Config -------------------------------------------------------

Write-Host ""
Write-Host "[6/7] Setting up environment config..." -ForegroundColor Yellow

$EnvExample = Join-Path $Root ".env.example"
$EnvFile = Join-Path $Root ".env"

if (-not (Test-Path $EnvFile)) {
    Copy-Item $EnvExample $EnvFile
    Write-Host "  OK .env created from .env.example" -ForegroundColor Green
    Write-Host ""
    Write-Host "  +-------------------------------------------------+" -ForegroundColor Yellow
    Write-Host "  |  ACTION REQUIRED: Edit .env and add your        |" -ForegroundColor Yellow
    Write-Host "  |  GROQ_API_KEY (free) or ANTHROPIC_API_KEY       |" -ForegroundColor Yellow
    Write-Host "  |  Get a free Groq key: https://console.groq.com  |" -ForegroundColor Yellow
    Write-Host "  +-------------------------------------------------+" -ForegroundColor Yellow
} else {
    Write-Host "  OK .env already exists" -ForegroundColor Green
}

# Copy .env to backend dir for uvicorn
Copy-Item $EnvFile (Join-Path $BackendDir ".env") -Force

# --- Output Directory ---------------------------------------------------------

Write-Host ""
Write-Host "[7/7] Creating ARIA output directory..." -ForegroundColor Yellow

$OutputDir = Join-Path $env:USERPROFILE "ARIA\outputs"
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
}
Write-Host "  OK Output directory: $OutputDir" -ForegroundColor Green

# --- Done ---------------------------------------------------------------------

Write-Host ""
Write-Host "+----------------------------------------------+" -ForegroundColor Green
Write-Host "|            Setup Complete!                    |" -ForegroundColor Green
Write-Host "+----------------------------------------------+" -ForegroundColor Green
Write-Host "|                                              |" -ForegroundColor Green
Write-Host "|  Next steps:                                 |" -ForegroundColor Green
Write-Host "|  1. Edit .env -> add your API key            |" -ForegroundColor Green
Write-Host "|  2. Run: .\scripts\start-dev.ps1             |" -ForegroundColor Green
Write-Host "|  3. Press Ctrl+Shift+Space to start!         |" -ForegroundColor Green
Write-Host "|                                              |" -ForegroundColor Green
Write-Host "+----------------------------------------------+" -ForegroundColor Green
Write-Host ""
