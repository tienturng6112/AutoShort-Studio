@echo off
title AutoShort Studio - Setup
cd /d "%~dp0"

echo ============================================
echo   AutoShort Studio - Environment Setup
echo ============================================
echo.

REM --- Check Python ---
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)
echo [OK] Python found.

REM --- Check Node.js ---
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not in PATH.
    echo Please install Node.js 18+ from https://nodejs.org/
    pause
    exit /b 1
)
echo [OK] Node.js found.

REM --- Check npm ---
where npm >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] npm is not available.
    pause
    exit /b 1
)
echo [OK] npm found.

echo.

REM --- Create Python virtual environment ---
if not exist "backend\venv\Scripts\python.exe" (
    echo [STEP] Creating Python virtual environment...
    python -m venv backend\venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created.
) else (
    echo [SKIP] Virtual environment already exists.
)

REM --- Install Python dependencies ---
echo [STEP] Installing Python dependencies...
backend\venv\Scripts\python.exe -m pip install --upgrade pip >nul 2>&1
backend\venv\Scripts\pip.exe install -r backend\requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Python dependencies.
    pause
    exit /b 1
)
echo [OK] Python dependencies installed.

REM --- Install Node.js dependencies ---
if not exist "frontend\node_modules" (
    echo [STEP] Installing Node.js dependencies...
    cd frontend
    call npm install
    if %errorlevel% neq 0 (
        cd ..
        echo [ERROR] Failed to install Node.js dependencies.
        pause
        exit /b 1
    )
    cd ..
    echo [OK] Node.js dependencies installed.
) else (
    echo [SKIP] Node.js dependencies already installed.
)

echo.
echo ============================================
echo   Setup complete!
echo   Run start.bat to launch AutoShort Studio.
echo ============================================
pause