@echo off
setlocal
echo DIAG2: dp0=[%~dp0]
echo DIAG2: launching start...
start "Northwind - FastAPI Server" /d "%~dp0src" cmd /k uvicorn api.main:app --port 8004
echo DIAG2: start errorlevel=%errorlevel%
set /a tries=0
:wait
curl -s -o nul "http://localhost:8004/static/admin/login.html"
if not errorlevel 1 goto ready
set /a tries+=1
if %tries% geq 10 ( echo DIAG2_FAIL & goto done )
timeout /t 1 /nobreak > nul
goto wait
:ready
echo DIAG2_OK
:done
