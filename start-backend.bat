@echo off
REM QR Attendance System - Backend Startup Script
REM This script starts the Django backend server

echo.
echo ====================================
echo QR Attendance - Backend Startup
echo ====================================
echo.

cd /d "%~dp0backend"

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)

echo [1/3] Checking virtual environment...
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

echo [2/3] Activating virtual environment...
call .venv\Scripts\activate.bat

echo [3/3] Starting Django server...
echo.
echo ✓ Backend server starting on http://0.0.0.0:8000
echo ✓ Press Ctrl+C to stop the server
echo.

python manage.py runserver 0.0.0.0:8000

pause
