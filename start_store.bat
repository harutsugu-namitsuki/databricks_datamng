@echo off
setlocal
set "URL=http://localhost:8000/static/store/login.html"

echo [Northwind] Starting FastAPI server (src/) ...
start "Northwind - FastAPI Server" /d "%~dp0src" cmd /k uvicorn api.main:app --reload --port 8000

echo [Northwind] Waiting for the server to come up ...
set /a tries=0
:wait
curl -s -o nul "%URL%"
if not errorlevel 1 goto ready
set /a tries+=1
if %tries% geq 30 (
  echo [Northwind] ERROR: server did not start.
  echo            Check the "Northwind - FastAPI Server" window for errors.
  goto end
)
timeout /t 1 /nobreak > nul
goto wait

:ready
echo [Northwind] Opening EC Store login page ...
start "" "%URL%"
echo [Northwind] Done. The server runs in the other window.

:end
echo.
echo (You can close this window. The server keeps running in its own window.)
pause
