@echo off
REM
REM Ketter 3.0 - Windows Uninstaller
REM Removes Ketter services
REM

echo Uninstalling Ketter 3.0...
echo.

REM Stop services
echo Stopping services...
nssm stop KetterAPI
nssm stop KetterWorker
nssm stop KetterFrontend

REM Remove services
echo Removing services...
nssm remove KetterAPI confirm
nssm remove KetterWorker confirm
nssm remove KetterFrontend confirm

echo.
echo [OK] Ketter services removed
echo.
echo Note: This does not remove:
echo   - PostgreSQL database 'ketter' (run: dropdb -U postgres ketter)
echo   - Python packages
echo   - Ketter source code directory
echo   - PostgreSQL, Redis, Node.js
echo.
pause
