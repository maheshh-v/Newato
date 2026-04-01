@echo off
echo Testing ARIA Components...
echo.

echo [1/3] Testing Backend...
curl -s http://127.0.0.1:8766/ping
if %errorlevel% == 0 (
    echo ✓ Backend is responding
) else (
    echo ✗ Backend not responding
)
echo.

echo [2/3] Testing Frontend...
curl -s -o nul -w "%%{http_code}" http://127.0.0.1:5173
if %errorlevel% == 0 (
    echo ✓ Frontend is responding
) else (
    echo ✗ Frontend not responding
)
echo.

echo [3/3] Opening test URLs...
echo Opening backend health: http://127.0.0.1:8766/health
start http://127.0.0.1:8766/health

echo Opening frontend overlay: http://127.0.0.1:5173/?window=overlay
start http://127.0.0.1:5173/?window=overlay

echo.
echo If both URLs open in your browser, the services are working!
pause