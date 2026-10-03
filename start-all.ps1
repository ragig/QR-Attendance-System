# QR Attendance System - Complete Startup Script (PowerShell)
# Usage: .\start-all.ps1

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "QR Attendance - Full System Startup" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ ERROR: Python is not installed" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check Node
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✓ Node: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ ERROR: Node.js is not installed" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check npm
try {
    $npmVersion = npm --version 2>&1
    Write-Host "✓ npm: $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ ERROR: npm is not installed" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "`nStarting services...`n" -ForegroundColor Yellow

# Start backend in new PowerShell window
Write-Host "[1/2] Starting backend on port 8000..." -ForegroundColor Yellow
$backendPath = Join-Path $PSScriptRoot "start-backend.ps1"
Start-Process powershell -ArgumentList @('-NoExit', '-File', $backendPath) -WindowStyle Normal

# Wait for backend to start
Start-Sleep -Seconds 3

# Start frontend in new PowerShell window
Write-Host "[2/2] Starting frontend on port 5175..." -ForegroundColor Yellow
$frontendPath = Join-Path $PSScriptRoot "start-frontend.ps1"
Start-Process powershell -ArgumentList @('-NoExit', '-File', $frontendPath) -WindowStyle Normal

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "Both services are starting!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Green

Write-Host "Backend:  http://127.0.0.1:8000/api/" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:5175" -ForegroundColor Cyan

Write-Host "`nTwo new windows should open. Keep them open while using the app." -ForegroundColor Yellow
Write-Host "To stop: Close both windows or press Ctrl+C in each window." -ForegroundColor Yellow
