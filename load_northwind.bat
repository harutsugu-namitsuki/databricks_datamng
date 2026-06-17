@echo off
setlocal
REM ---------------------------------------------------------------------------
REM One-time / re-load: create the local "northwind" database and load data.
REM Data source: docs/design/data_platform/northwind.sql (same as production RDS)
REM Auto-detects psql under "C:\Program Files\PostgreSQL\*\bin".
REM ---------------------------------------------------------------------------

set "PGUSER=postgres"
set "PGHOST=localhost"
set "PGPORT=5432"
REM Local dev DB password (matches db.py default). Change here if yours differs.
set "PGPASSWORD=postgres"
set "SQLFILE=%~dp0docs\design\data_platform\northwind.sql"

REM --- locate psql: PATH first, then standard install dirs -------------------
set "PSQL="
for %%P in (psql.exe) do if not defined PSQL set "PSQL=%%~$PATH:P"
if not defined PSQL (
  for /f "delims=" %%P in ('dir /b /s "C:\Program Files\PostgreSQL\*\bin\psql.exe" 2^>nul') do set "PSQL=%%P"
)
if not defined PSQL (
  echo ERROR: psql.exe not found ^(PATH or C:\Program Files\PostgreSQL\*^).
  goto end
)
echo Using psql: %PSQL%

echo [1/2] Creating database "northwind" (ignored if it already exists) ...
"%PSQL%" -U %PGUSER% -h %PGHOST% -p %PGPORT% -c "CREATE DATABASE northwind;"

echo [2/2] Loading schema and data ...
"%PSQL%" -U %PGUSER% -h %PGHOST% -p %PGPORT% -d northwind -v ON_ERROR_STOP=1 -f "%SQLFILE%"
if errorlevel 1 (
  echo ERROR: loading failed. See messages above.
  goto end
)

echo.
echo Done. Now run start_store.bat or start_admin.bat.

:end
echo.
pause
