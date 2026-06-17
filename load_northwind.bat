@echo off
setlocal
REM ---------------------------------------------------------------------------
REM One-time: create the local "northwind" database and load Northwind data.
REM Run this AFTER installing PostgreSQL locally (psql must be on PATH).
REM Data source: docs/design/data_platform/northwind.sql (same as production RDS)
REM ---------------------------------------------------------------------------

set "PGUSER=postgres"
set "PGHOST=localhost"
set "PGPORT=5432"
set "SQLFILE=%~dp0docs\design\data_platform\northwind.sql"

where psql >nul 2>&1
if errorlevel 1 (
  echo ERROR: psql not found on PATH.
  echo        Install PostgreSQL first, or add its bin\ folder to PATH.
  goto end
)

echo This creates database "northwind" on %PGHOST%:%PGPORT% (user: %PGUSER%)
echo and loads it from:
echo   %SQLFILE%
echo You will be prompted for the postgres password.
echo.

echo [1/2] Creating database "northwind" (ignored if it already exists) ...
psql -U %PGUSER% -h %PGHOST% -p %PGPORT% -c "CREATE DATABASE northwind;"

echo [2/2] Loading schema and data ...
psql -U %PGUSER% -h %PGHOST% -p %PGPORT% -d northwind -f "%SQLFILE%"
if errorlevel 1 (
  echo ERROR: loading failed. See messages above.
  goto end
)

echo.
echo Done. Now run start_store.bat or start_admin.bat.

:end
echo.
pause
