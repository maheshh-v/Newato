# ARIA Dev Start Script (Windows PowerShell)
# Starts the Python backend + React dev server + Electron simultaneously.

$ErrorActionPreference = "Continue"
$Root = Split-Path $PSScriptRoot -Parent
$BackendDir = Join-Path $Root "backend"
$FrontendDir = Join-Path $Root "frontend"
$ElectronDir = Join-Path $Root "electron"

Write-Host "Starting ARIA Dev Environment" -ForegroundColor Cyan

# Copy root .env to backend dir
$EnvSrc = Join-Path $Root ".env"
$EnvDst = Join-Path $BackendDir ".env"
if (Test-Path $EnvSrc) {
    Copy-Item $EnvSrc $EnvDst -Force
}

$PythonBin = Join-Path $BackendDir "venv\Scripts\python.exe"
if (-not (Test-Path $PythonBin)) {
    Write-Error "Python venv not found. Run .\scripts\setup.ps1 first."
    exit 1
}

Write-Host "Starting ARIA backend (port 8765)..." -ForegroundColor Yellow
$BackendJob = Start-Job -ScriptBlock {
    param($dir, $python)
    Set-Location $dir
    try {
        & $python -m uvicorn main:app --host 127.0.0.1 --port 8765 --reload
    } catch {
        Write-Error "Backend failed: $_"
    }
} -ArgumentList $BackendDir, $PythonBin

Write-Host "Starting React dev server (port 5173)..." -ForegroundColor Yellow
$FrontendJob = Start-Job -ScriptBlock {
    param($dir)
    Set-Location $dir
    try {
        npm run dev
    } catch {
        Write-Error "Frontend failed: $_"
    }
} -ArgumentList $FrontendDir

Write-Host "Waiting for servers to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 4

Write-Host "Starting Electron..." -ForegroundColor Yellow
Set-Location $ElectronDir
$env:ELECTRON_DEV = "true"
npx electron . --dev

Write-Host "Electron closed. Backend and frontend are still running." -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop all services." -ForegroundColor Yellow

# Keep the script running so backend/frontend stay alive
while ($true) {
    Start-Sleep -Seconds 2
}

# Cleanup on exit
Write-Host "Shutting down..." -ForegroundColor Yellow
Stop-Job $BackendJob, $FrontendJob -ErrorAction SilentlyContinue
Remove-Job $BackendJob, $FrontendJob -ErrorAction SilentlyContinue
Write-Host "Done" -ForegroundColor Green
