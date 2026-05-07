@echo off
REM Complete test runner for microservicios project
REM Run this from the proyectooperaciones directory

echo.
echo ============================================================
echo MICROSERVICIOS TEST & INTEGRATION SUITE
echo ============================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found. Please install Python and add it to PATH.
    pause
    exit /b 1
)

REM Check if postgres is running
echo Checking PostgreSQL connection...
python -c "import psycopg; psycopg.connect('postgresql://user:password@localhost:5432/transactions_db').close(); print('OK')" >nul 2>&1
if errorlevel 1 (
    echo Error: Cannot connect to PostgreSQL at localhost:5432
    echo Make sure postgres is running with credentials: user/password
    pause
    exit /b 1
)
echo PostgreSQL is available.

echo.
echo Running integration tests...
python run_integration_tests.py

if errorlevel 1 (
    echo.
    echo Tests failed with exit code %errorlevel%
    pause
    exit /b 1
) else (
    echo.
    echo Tests completed successfully!
    pause
    exit /b 0
)
