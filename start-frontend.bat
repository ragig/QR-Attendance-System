@echo off
REM QR Attendance System - Frontend Startup Script
REM This script starts the Vite frontend server

echo.
echo ====================================
echo QR Attendance - Frontend Startup
echo ====================================
echo.

cd /d "%~dp0my-app"

REM Check if Node is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js 16+ from https://nodejs.org/
    pause
    exit /b 1
)

REM Check if npm is installed
npm --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: npm is not installed
    pause
    exit /b 1
)

echo [1/2] Checking dependencies...
if not exist "node_modules" (
    echo Installing npm dependencies...
    call npm install
    if errorlevel 1 (
        echo ERROR: npm install failed
        pause
        exit /b 1
    )
)

echo [2/2] Starting Vite server...
echo.
echo ✓ Frontend server starting on http://localhost:5175
echo ✓ Press Ctrl+C to stop the server
echo.

call npm run dev

pause
