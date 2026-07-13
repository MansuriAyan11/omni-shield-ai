# PowerShell script to start both frontend and backend servers
# Run from project root: .\start_servers.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "OmniShield - Starting Servers" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if migration was done
if (-not (Test-Path "frontend\package.json")) {
    Write-Host "✗ Frontend not found! Run .\migrate_frontend.ps1 first" -ForegroundColor Red
    exit 1
}

# Function to check if port is in use
function Test-Port {
    param($Port)
    $connection = Test-NetConnection -ComputerName localhost -Port $Port -WarningAction SilentlyContinue -InformationLevel Quiet
    return $connection
}

# Check ports
Write-Host "Checking ports..." -ForegroundColor Yellow
if (Test-Port 8000) {
    Write-Host "  ⚠ Port 8000 already in use (Backend)" -ForegroundColor Yellow
}
if (Test-Port 3000) {
    Write-Host "  ⚠ Port 3000 already in use (Frontend)" -ForegroundColor Yellow
}
Write-Host ""

# Start Backend
Write-Host "[1/2] Starting Backend Server..." -ForegroundColor Cyan
Write-Host "  → http://localhost:8000" -ForegroundColor Gray
Write-Host "  → API Docs: http://localhost:8000/docs" -ForegroundColor Gray

$backendProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
Set-Location '$PWD\backend'
Write-Host '========================================' -ForegroundColor Green
Write-Host 'Backend Server Starting...' -ForegroundColor Green
Write-Host '========================================' -ForegroundColor Green
Write-Host ''
if (Test-Path 'venv\Scripts\activate.ps1') {
    .\venv\Scripts\activate
    python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
} else {
    Write-Host '✗ Virtual environment not found!' -ForegroundColor Red
    Write-Host 'Run: python -m venv venv' -ForegroundColor Yellow
    Write-Host 'Then: .\venv\Scripts\activate' -ForegroundColor Yellow
    Write-Host 'Then: pip install -r requirements.txt' -ForegroundColor Yellow
    pause
}
"@ -PassThru

Start-Sleep -Seconds 2

# Start Frontend
Write-Host ""
Write-Host "[2/2] Starting Frontend Server..." -ForegroundColor Cyan
Write-Host "  → http://localhost:3000" -ForegroundColor Gray

$frontendProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
Set-Location '$PWD\frontend'
Write-Host '========================================' -ForegroundColor Green
Write-Host 'Frontend Server Starting...' -ForegroundColor Green
Write-Host '========================================' -ForegroundColor Green
Write-Host ''
if (Test-Path 'node_modules') {
    npm run dev
} else {
    Write-Host '✗ Dependencies not installed!' -ForegroundColor Red
    Write-Host 'Installing dependencies...' -ForegroundColor Yellow
    npm install
    Write-Host ''
    Write-Host '✓ Installation complete!' -ForegroundColor Green
    Write-Host 'Starting dev server...' -ForegroundColor Green
    npm run dev
}
"@ -PassThru

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Servers Started!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "URLs:" -ForegroundColor Cyan
Write-Host "  Frontend:  http://localhost:3000" -ForegroundColor White
Write-Host "  Backend:   http://localhost:8000" -ForegroundColor White
Write-Host "  API Docs:  http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C in each terminal to stop servers" -ForegroundColor Yellow
Write-Host ""
