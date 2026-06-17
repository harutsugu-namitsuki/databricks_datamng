@echo off
chcp 65001 > nul
echo DIAG: dp0=[%~dp0]
echo DIAG: target dir=[%~dp0src]
echo DIAG: launching start...
start "Northwind - FastAPI Server" /d "%~dp0src" cmd /k uvicorn api.main:app --port 8003
echo DIAG: start returned errorlevel=%errorlevel%
set /a tries=0
:wait
curl -s -o nul "http://localhost:8003/static/admin/login.html"
echo DIAG: curl errorlevel=%errorlevel% tries=%tries%
if not errorlevel 1 goto ready
set /a tries+=1
if %tries% geq 8 ( echo DIAG_FAIL & goto done )
timeout /t 1 /nobreak > nul
goto wait
:ready
echo DIAG_OK
:done
