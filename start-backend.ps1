# QR Attendance System - Backend Startup Script (PowerShell)
# Usage: .\start-backend.ps1

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "QR Attendance - Backend Startup" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ ERROR: Python is not installed" -ForegroundColor Red
    Write-Host "Please install Python 3.10+ from https://www.python.org/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Change to backend directory
Push-Location (Join-Path $PSScriptRoot "backend")

# Create virtual environment if it doesn't exist
if (-not (Test-Path ".venv")) {
    Write-Host "[1/3] Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}

Write-Host "[2/3] Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

Write-Host "[3/3] Starting Django server..." -ForegroundColor Yellow
Write-Host "`n✓ Backend server starting on http://0.0.0.0:8000" -ForegroundColor Green
Write-Host "✓ Press Ctrl+C to stop the server`n" -ForegroundColor Green

python manage.py runserver 0.0.0.0:8000

Pop-Location
