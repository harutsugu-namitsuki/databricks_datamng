@echo off
chcp 65001 > nul
start "Northwind - FastAPI Server" /d "%~dp0src" cmd /k uvicorn api.main:app --port 8002
set /a tries=0
:wait
curl -s -o nul "http://localhost:8002/static/admin/login.html"
if not errorlevel 1 goto ready
set /a tries+=1
if %tries% geq 20 ( echo TEST_FAIL & exit /b 1 )
timeout /t 1 /nobreak > nul
goto wait
:ready
echo TEST_OK
