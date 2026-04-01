# ARIA Dev Start Script (Windows PowerShell)
# Starts the Python backend + React dev server + Electron simultaneously.

$ErrorActionPreference = "Continue"
$Root = Split-Path $PSScriptRoot -Parent
$BackendDir = Join-Path $Root "backend"
$FrontendDir = Join-Path $Root "frontend"
$ElectronDir = Join-Path $Root "electron"

Write-Host ""
Write-Host "+----------------------------------------------+" -ForegroundColor Cyan
Write-Host "|         ARIA - Dev Environment               |" -ForegroundColor Cyan
Write-Host "+----------------------------------------------+" -ForegroundColor Cyan
Write-Host ""

# --- Step 0: Kill Zombie Processes --------------------------------------------
Write-Host "Cleaning up old sessions..." -ForegroundColor Yellow
$Ports = @(8765, 5173)
foreach ($Port in $Ports) {
    # Get any process ID listening on these ports
    $Connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    if ($Connections) {
        foreach ($Conn in $Connections) {
            $TargetPID = $Conn.OwningProcess
            if ($TargetPID -and $TargetPID -ne $PID) {
                Write-Host "  OK Killing old process $PID on port $Port" -ForegroundColor DarkGray
                Stop-Process -Id $PID -Force -ErrorAction SilentlyContinue
            }
        }
    }
}
Write-Host "  OK Cleanup complete" -ForegroundColor Green

# --- Pre-flight checks ---
$EnvSrc = Join-Path $Root ".env"
$EnvDst = Join-Path $BackendDir ".env"
if (Test-Path $EnvSrc) {
    Copy-Item $EnvSrc $EnvDst -Force
    Write-Host "  OK .env synced" -ForegroundColor Green
}

$PythonBin = Join-Path $BackendDir "venv\Scripts\python.exe"
if (-not (Test-Path $PythonBin)) {
    Write-Error "Python venv not found. Run .\scripts\setup.ps1 first."
    exit 1
}

# --- Start Jobs ---
Write-Host ""
Write-Host "[1/3] Launching backend..." -ForegroundColor Yellow
$BackendJob = Start-Job -ScriptBlock {
    param($dir, $python)
    $ErrorActionPreference = "Continue"
    Set-Location $dir
    try {
        & $python -m uvicorn main:app --host 127.0.0.1 --port 8765 --reload
    } catch {
        Write-Error "Backend failed: $_"
    }
} -ArgumentList $BackendDir, $PythonBin

Write-Host "[2/3] Launching frontend..." -ForegroundColor Yellow
$FrontendJob = Start-Job -ScriptBlock {
    param($dir)
    $ErrorActionPreference = "Continue"
    Set-Location $dir
    try {
        npm run dev
    } catch {
        Write-Error "Frontend failed: $_"
    }
} -ArgumentList $FrontendDir

# --- Wait for Ping ---
Write-Host ""
Write-Host "Waiting for services to respond..." -ForegroundColor Yellow
$waited = 0
$ready = $false
while ($waited -lt 45) {
    Start-Sleep -Seconds 1
    $waited++
    try {
        # Check /ping (it was added to main.py recently)
        $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8765/ping" -UseBasicParsing -TimeoutSec 1 -ErrorAction SilentlyContinue
        if ($resp -and $resp.StatusCode -eq 200) { $ready = $true; break }
    } catch { }
}

if ($ready) {
    Write-Host "  OK Backend is responding!" -ForegroundColor Green
} else {
    Write-Host "  WARN Backend is slow. Continuing to Electron..." -ForegroundColor Yellow
}

# --- Start Electron ---
Write-Host ""
Write-Host "[3/3] Starting Electron..." -ForegroundColor Yellow
Write-Host ""
Write-Host "  +-------------------------------------------------+" -ForegroundColor Green
Write-Host "  |  READY! Press Ctrl + Shift + Space to toggle    |" -ForegroundColor Green
Write-Host "  |  the AI overlay from anywhere.                  |" -ForegroundColor Green
Write-Host "  +-------------------------------------------------+" -ForegroundColor Green
Write-Host ""

Push-Location $ElectronDir
$env:ELECTRON_DEV = "true"

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
