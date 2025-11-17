@echo off
REM
REM Ketter 3.0 - Windows Native Installer
REM Installs Ketter as a native Windows application with full filesystem access
REM
REM Usage: Run as Administrator
REM

setlocal enabledelayedexpansion

echo ================================================
echo   Ketter 3.0 - Windows Native Installer
echo   Production-Grade File Transfer System
echo ================================================
echo.

REM Check if running as Administrator
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo ERROR: This script must be run as Administrator
    echo Right-click install.bat and select "Run as administrator"
    pause
    exit /b 1
)

echo Checking system requirements...
echo.

REM Check Windows version
for /f "tokens=4-5 delims=. " %%i in ('ver') do set VERSION=%%i.%%j
echo [OK] Windows version: %VERSION%

REM Check if Python is installed
python --version >nul 2>&1
if %errorLevel% NEQ 0 (
    echo [!] Python not found. Installing Python 3.11...
    echo.
    echo Please download and install Python 3.11 from:
    echo https://www.python.org/downloads/windows/
    echo.
    echo IMPORTANT: Check "Add Python to PATH" during installation
    pause
    start https://www.python.org/downloads/windows/
    exit /b 1
) else (
    for /f "tokens=2" %%i in ('python --version') do echo [OK] Python version: %%i
)

REM Check if PostgreSQL is installed
psql --version >nul 2>&1
if %errorLevel% NEQ 0 (
    echo [!] PostgreSQL not found. Installing PostgreSQL 15...
    echo.
    echo Please download and install PostgreSQL 15 from:
    echo https://www.postgresql.org/download/windows/
    echo.
    echo IMPORTANT: Remember the password you set for 'postgres' user
    pause
    start https://www.postgresql.org/download/windows/
    exit /b 1
) else (
    for /f "tokens=3" %%i in ('psql --version') do echo [OK] PostgreSQL version: %%i
)

REM Check if Redis is installed
redis-server --version >nul 2>&1
if %errorLevel% NEQ 0 (
    echo [!] Redis not found. Installing Redis...
    echo.
    echo Please download and install Redis from:
    echo https://github.com/microsoftarchive/redis/releases
    echo Download: Redis-x64-3.0.504.msi
    pause
    start https://github.com/microsoftarchive/redis/releases
    exit /b 1
) else (
    echo [OK] Redis installed
)

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorLevel% NEQ 0 (
    echo [!] Node.js not found. Installing Node.js 20...
    echo.
    echo Please download and install Node.js 20 LTS from:
    echo https://nodejs.org/
    pause
    start https://nodejs.org/
    exit /b 1
) else (
    for /f %%i in ('node --version') do echo [OK] Node.js version: %%i
)

REM Check if NSSM is installed (for Windows services)
nssm version >nul 2>&1
if %errorLevel% NEQ 0 (
    echo [!] NSSM (Non-Sucking Service Manager) not found
    echo.
    echo Downloading NSSM...
    powershell -Command "Invoke-WebRequest -Uri 'https://nssm.cc/release/nssm-2.24.zip' -OutFile '%TEMP%\nssm.zip'"
    powershell -Command "Expand-Archive -Path '%TEMP%\nssm.zip' -DestinationPath '%TEMP%\nssm' -Force"

    REM Copy nssm.exe to Windows directory
    if exist "%TEMP%\nssm\nssm-2.24\win64\nssm.exe" (
        copy "%TEMP%\nssm\nssm-2.24\win64\nssm.exe" "C:\Windows\System32\" >nul
        echo [OK] NSSM installed
    ) else (
        echo [ERROR] Failed to install NSSM
        pause
        exit /b 1
    )
) else (
    echo [OK] NSSM installed
)

echo.
echo Installing Ketter dependencies...
echo.

REM Get Ketter directory (script should be in installers\windows\)
cd /d "%~dp0..\.."
set KETTER_DIR=%CD%

echo Ketter directory: %KETTER_DIR%

REM Install Python dependencies
echo Installing Python packages...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

REM Install frontend dependencies
echo Installing frontend packages...
cd frontend
call npm install
cd ..

echo.
echo Setting up database...
echo.

REM Create Ketter database
psql -U postgres -lqt | find /i "ketter" >nul
if %errorLevel% NEQ 0 (
    echo Creating 'ketter' database...
    psql -U postgres -c "CREATE DATABASE ketter;"
    if %errorLevel% NEQ 0 (
        echo [ERROR] Failed to create database. Check PostgreSQL password.
        pause
        exit /b 1
    )
    echo [OK] Database created
) else (
    echo [OK] Database 'ketter' already exists
)

REM Run migrations
echo Running database migrations...
alembic upgrade head

echo.
echo Creating Ketter Windows services...
echo.

REM Stop existing services if they exist
nssm stop KetterAPI >nul 2>&1
nssm stop KetterWorker >nul 2>&1
nssm stop KetterFrontend >nul 2>&1

REM Remove existing services
nssm remove KetterAPI confirm >nul 2>&1
nssm remove KetterWorker confirm >nul 2>&1
nssm remove KetterFrontend confirm >nul 2>&1

REM Get Python and node paths
for /f "delims=" %%i in ('where python') do set PYTHON_PATH=%%i
for /f "delims=" %%i in ('where node') do set NODE_PATH=%%i
for /f "delims=" %%i in ('where npm') do set NPM_PATH=%%i

REM Install Ketter API service
echo Installing Ketter API service...
nssm install KetterAPI "%PYTHON_PATH%" "-m" "uvicorn" "app.main:app" "--host" "0.0.0.0" "--port" "8000"
nssm set KetterAPI AppDirectory "%KETTER_DIR%"
nssm set KetterAPI AppEnvironmentExtra DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ketter REDIS_URL=redis://localhost:6379/0
nssm set KetterAPI DisplayName "Ketter API"
nssm set KetterAPI Description "Ketter 3.0 File Transfer API"
nssm set KetterAPI Start SERVICE_AUTO_START
nssm set KetterAPI AppStdout "%KETTER_DIR%\logs\api.log"
nssm set KetterAPI AppStderr "%KETTER_DIR%\logs\api-error.log"

REM Install Ketter Worker service
echo Installing Ketter Worker service...
nssm install KetterWorker "%PYTHON_PATH%" "-m" "rq" "worker" "--url" "redis://localhost:6379/0" "default"
nssm set KetterWorker AppDirectory "%KETTER_DIR%"
nssm set KetterWorker AppEnvironmentExtra DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ketter REDIS_URL=redis://localhost:6379/0
nssm set KetterWorker DisplayName "Ketter Worker"
nssm set KetterWorker Description "Ketter 3.0 Transfer Worker"
nssm set KetterWorker Start SERVICE_AUTO_START
nssm set KetterWorker AppStdout "%KETTER_DIR%\logs\worker.log"
nssm set KetterWorker AppStderr "%KETTER_DIR%\logs\worker-error.log"

REM Install Ketter Frontend service
echo Installing Ketter Frontend service...
nssm install KetterFrontend "%NPM_PATH%" "run" "dev"
nssm set KetterFrontend AppDirectory "%KETTER_DIR%\frontend"
nssm set KetterFrontend DisplayName "Ketter Frontend"
nssm set KetterFrontend Description "Ketter 3.0 Web Interface"
nssm set KetterFrontend Start SERVICE_AUTO_START
nssm set KetterFrontend AppStdout "%KETTER_DIR%\logs\frontend.log"
nssm set KetterFrontend AppStderr "%KETTER_DIR%\logs\frontend-error.log"

REM Create logs directory
if not exist "%KETTER_DIR%\logs" mkdir "%KETTER_DIR%\logs"

echo [OK] Services installed

echo.
echo Starting Ketter services...
echo.

REM Start Redis (if not running as service)
sc query Redis | find "RUNNING" >nul
if %errorLevel% NEQ 0 (
    echo Starting Redis...
    start /B redis-server
    timeout /t 2 /nobreak >nul
)

REM Start PostgreSQL (if not running as service)
sc query postgresql-x64-15 | find "RUNNING" >nul
if %errorLevel% NEQ 0 (
    echo PostgreSQL should be running. Check Services (services.msc)
)

REM Start Ketter services
nssm start KetterAPI
nssm start KetterWorker
nssm start KetterFrontend

echo [OK] Services started

REM Wait for services to initialize
echo.
echo Waiting for services to initialize (15 seconds)...
timeout /t 15 /nobreak >nul

REM Check if services are running
echo.
echo Checking service status...
echo.

nssm status KetterAPI | find "SERVICE_RUNNING" >nul
if %errorLevel% EQU 0 (
    echo [OK] API service running
) else (
    echo [!] API service not running - check logs\api-error.log
)

nssm status KetterWorker | find "SERVICE_RUNNING" >nul
if %errorLevel% EQU 0 (
    echo [OK] Worker service running
) else (
    echo [!] Worker service not running - check logs\worker-error.log
)

nssm status KetterFrontend | find "SERVICE_RUNNING" >nul
if %errorLevel% EQU 0 (
    echo [OK] Frontend service running
) else (
    echo [!] Frontend service not running - check logs\frontend-error.log
)

echo.
echo ================================================
echo [OK] Ketter 3.0 Installation Complete!
echo ================================================
echo.
echo Access Ketter at: http://localhost:3000
echo.
echo Useful commands:
echo    View logs:       notepad %KETTER_DIR%\logs\api.log
echo    Restart API:     nssm restart KetterAPI
echo    Stop services:   nssm stop KetterAPI KetterWorker KetterFrontend
echo    Start services:  nssm start KetterAPI KetterWorker KetterFrontend
echo    Service status:  nssm status KetterAPI
echo.
echo Configuration file: %KETTER_DIR%\ketter.config.yml
echo.
echo Open your browser to http://localhost:3000
echo.
pause
