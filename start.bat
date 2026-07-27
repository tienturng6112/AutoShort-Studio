@echo off
title AutoShort Studio
cd /d "%~dp0"

REM --- Check if environment is set up ---
if not exist "backend\venv\Scripts\python.exe" (
    echo [AutoShort Studio] Environment not set up.
    echo Please run setup.bat first to install dependencies.
    pause
    exit /b 1
)

if not exist "frontend\node_modules" (
    echo [AutoShort Studio] Frontend dependencies not found.
    echo Please run setup.bat first to install dependencies.
    pause
    exit /b 1
)

REM --- Start the application ---
backend\venv\Scripts\python.exe desktop_app.py
pause