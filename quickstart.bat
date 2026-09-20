@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title HealthPals Quickstart

:menu
cls
echo ==========================================
echo            HealthPals - Quickstart
echo ==========================================
echo.
echo   Your friendly desktop health companion.
echo.
echo   [1]  Start HealthPals
echo   [2]  Stop HealthPals
echo   [3]  Build standalone HealthPals.exe
echo   [4]  Exit this menu
echo.
set "choice="
set /p choice="Select an option (1-4): "

if "%choice%"=="1" goto start
if "%choice%"=="2" goto stop
if "%choice%"=="3" goto build
if "%choice%"=="4" goto end
echo.
echo Please choose 1, 2, 3, or 4.
timeout /t 2 >nul
goto menu

:start
echo.
if not exist ".venv\Scripts\pythonw.exe" (
    echo Creating virtual environment ^(first run^)...
    python -m venv .venv
    if errorlevel 1 (
        echo.
        echo ERROR: Could not create the virtual environment.
        echo Make sure Python 3.10+ is installed and on your PATH.
        echo.
        pause
        goto menu
    )
)

echo Installing / updating requirements...
".venv\Scripts\python.exe" -m pip install -r requirements.txt --quiet --disable-pip-version-check
if errorlevel 1 (
    echo.
    echo ERROR: Failed to install requirements.
    echo.
    pause
    goto menu
)

echo Launching HealthPals...
start "" ".venv\Scripts\pythonw.exe" "run.py"
echo.
echo HealthPals is now running in your system tray.
echo Double-click the tray icon to open the dashboard.
echo.
pause
goto menu

:stop
echo.
echo Stopping HealthPals...
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='pythonw.exe' -or Name='HealthPals.exe'\" | Where-Object { $_.CommandLine -like '*run.py*' -or $_.Name -eq 'HealthPals.exe' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
echo Done. HealthPals has been stopped.
echo.
pause
goto menu

:build
echo.
if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment ^(first run^)...
    python -m venv .venv
)
echo Installing build dependencies...
".venv\Scripts\python.exe" -m pip install -r requirements.txt pyinstaller pillow --quiet --disable-pip-version-check
echo Building standalone HealthPals.exe...
".venv\Scripts\pyinstaller.exe" HealthPals.spec
if errorlevel 1 (
    echo.
    echo ERROR: Build failed.
    echo.
    pause
    goto menu
)
echo.
echo SUCCESS: HealthPals.exe has been compiled to dist\HealthPals.exe!
echo You may launch it directly from there.
echo.
pause
goto menu

:end
endlocal
exit /b 0
