# QR Attendance System - Frontend Startup Script (PowerShell)
# Usage: .\start-frontend.ps1

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "QR Attendance - Frontend Startup" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if Node is installed
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✓ Node: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ ERROR: Node.js is not installed" -ForegroundColor Red
    Write-Host "Please install Node.js 16+ from https://nodejs.org/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if npm is installed
try {
    $npmVersion = npm --version 2>&1
    Write-Host "✓ npm: $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ ERROR: npm is not installed" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Change to frontend directory
Push-Location (Join-Path $PSScriptRoot "my-app")

# Detect LAN IP for device-friendly QR links
try {
    $localIp = Get-NetIPAddress -AddressFamily IPv4 |
        Where-Object { $_.IPAddress -notmatch '^(127|169)\.' } |
        Select-Object -ExpandProperty IPAddress -First 1
    if (-not $localIp) { throw "No LAN IP found" }
    $env:VITE_PUBLIC_APP_URL = "http://$localIp:5175"
    Write-Host "✓ Device QR uses app origin: $env:VITE_PUBLIC_APP_URL" -ForegroundColor Green
} catch {
    $env:VITE_PUBLIC_APP_URL = 'http://localhost:5175'
    Write-Host "⚠️ Could not detect LAN IP; falling back to localhost." -ForegroundColor Yellow
}

# Install dependencies if needed
if (-not (Test-Path "node_modules")) {
    Write-Host "`n[1/2] Installing npm dependencies..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ ERROR: npm install failed" -ForegroundColor Red
        Pop-Location
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host "[2/2] Starting Vite server..." -ForegroundColor Yellow
Write-Host "`n✓ Frontend server starting on $env:VITE_PUBLIC_APP_URL" -ForegroundColor Green
Write-Host "✓ Press Ctrl+C to stop the server`n" -ForegroundColor Green

npm run dev

Pop-Location
