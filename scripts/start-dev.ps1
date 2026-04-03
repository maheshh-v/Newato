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
                Write-Host "  OK Killing old process $TargetPID on port $Port" -ForegroundColor DarkGray
                Stop-Process -Id $TargetPID -Force -ErrorAction SilentlyContinue
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
    # Try system Python if venv doesn't exist
    $PythonBin = "python"
    try {
        & python --version > $null 2>&1
        Write-Host "  OK Using system Python" -ForegroundColor Green
    } catch {
        Write-Error "Neither venv nor system Python found. Please install Python 3.10+"
        exit 1
    }
}

# --- Start Jobs ---
Write-Host ""
Write-Host "[1/3] Launching backend..." -ForegroundColor Yellow
$BackendJob = Start-Job -ScriptBlock {
    param($dir, $python)
    $ErrorActionPreference = "Continue"
    Set-Location $dir
    
    Write-Output "[Backend] Starting with Python: $python"
    Write-Output "[Backend] Current directory: $(Get-Location)"
    Write-Output "[Backend] Python version:"
    & $python --version
    
    try {
        # Run without --reload to avoid port binding issues on Windows
        Write-Output "[Backend] Launching uvicorn..."
        & $python -m uvicorn main:app --host 127.0.0.1 --port 8765 2>&1
    } catch {
        Write-Output "[Backend] ERROR: $_"
        throw $_
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

# --- Wait for Services ---
Write-Host ""
Write-Host "Waiting for backend to start on port 8765..." -ForegroundColor Yellow
$waited = 0
$ready = $false
while ($waited -lt 60) {
    Start-Sleep -Seconds 1
    $waited++
    
    # Check if port 8765 is listening
    try {
        $backendReady = Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue
        if ($backendReady) {
            Write-Host "  ✅ Backend listening on port 8765!" -ForegroundColor Green
            $ready = $true
            break
        }
    } catch {
        # Port check failed, continue waiting
    }
    
    # Also try HTTP health check
    try {
        $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8765/health" -UseBasicParsing -TimeoutSec 1 -ErrorAction SilentlyContinue
        if ($resp -and $resp.StatusCode -eq 200) {
            Write-Host "  ✅ Backend responding to /health!" -ForegroundColor Green
            $ready = $true
            break
        }
    } catch {
        # Continue waiting
    }
}

if (-not $ready) {
    Write-Host "  ⚠️ Backend startup slow (60s timeout). Checking job status..." -ForegroundColor Yellow
    $backendJobState = Get-Job -Id $BackendJob.Id | Select-Object -ExpandProperty State
    Write-Host "  Backend job state: $backendJobState" -ForegroundColor Yellow
    
    if ($backendJobState -ne "Running") {
        Write-Host "  ❌ Backend job failed!" -ForegroundColor Red
        Write-Host "  Output:" -ForegroundColor Red
        Get-Job -Id $BackendJob.Id | Receive-Job
        Write-Error "Backend failed to start. Check output above."
        exit 1
    }
    
    # Show last few lines of output
    $output = Get-Job -Id $BackendJob.Id | Receive-Job -Keep
    if ($output) {
        Write-Host "  Backend output (last 10 lines):" -ForegroundColor Yellow
        $output | Select-Object -Last 10 | ForEach-Object { Write-Host "    $_" }
    }
}

Write-Host ""
Write-Host "[3/3] Starting Electron in dev mode..." -ForegroundColor Yellow
Write-Host ""
Write-Host "  +-------------------------------------------------+" -ForegroundColor Green
Write-Host "  |  READY! Press Ctrl + Shift + Space to toggle    |" -ForegroundColor Green
Write-Host "  |  the AI overlay from anywhere.                  |" -ForegroundColor Green
Write-Host "  +-------------------------------------------------+" -ForegroundColor Green
Write-Host ""

# Run Electron in dev mode (use fullpath since we're in root dir)
& npx electron $ElectronDir --dev

Write-Host ""
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
