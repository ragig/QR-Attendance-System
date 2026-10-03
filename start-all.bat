@echo off
REM QR Attendance System - Complete Startup Script
REM This script starts both backend and frontend in separate windows

echo.
echo ====================================
echo QR Attendance - Full System Startup
echo ====================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed. Please install Python 3.10+
    pause
    exit /b 1
)

REM Check Node
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed. Please install Node.js 16+
    pause
    exit /b 1
)

echo ✓ Python version: 
python --version
echo.
echo ✓ Node version:
node --version
echo.
echo ✓ npm version:
npm --version
echo.

echo Starting services...
echo.

REM Start backend in new window
echo [1/2] Starting backend on port 8000...
start "QR Attendance - Backend" "%~dp0start-backend.bat"

REM Wait for backend to start
timeout /t 3 /nobreak

REM Start frontend in new window
echo [2/2] Starting frontend on port 5175...
start "QR Attendance - Frontend" "%~dp0start-frontend.bat"

echo.
echo ====================================
echo Both services are starting!
echo ====================================
echo.
echo Backend:  http://127.0.0.1:8000/api/
echo Frontend: http://localhost:5175
echo.
echo Two new windows should open. Keep them open while using the app.
echo.
echo To stop:
echo   - Close both windows, or
echo   - Press Ctrl+C in each window
echo.
pause
