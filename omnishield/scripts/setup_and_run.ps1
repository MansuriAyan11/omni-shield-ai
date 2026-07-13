# Complete setup and run script for OmniShield
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "OmniShield - Complete Setup & Run" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Initialize Database
Write-Host "[1/3] Initializing Database..." -ForegroundColor Yellow
Set-Location "$PSScriptRoot\backend"

if (-not (Test-Path "venv\Scripts\python.exe")) {
    Write-Host "✗ Virtual environment not found in backend!" -ForegroundColor Red
    Write-Host "Please run: cd backend; python -m venv venv; .\venv\Scripts\activate; pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

Write-Host "  Creating database tables..." -ForegroundColor Gray
& ".\venv\Scripts\python.exe" "create_tables.py"

if (Test-Path "moderation.db") {
    $dbSize = (Get-Item "moderation.db").Length
    Write-Host "  ✓ Database ready: moderation.db ($dbSize bytes)" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Database file not found, will be created on first run" -ForegroundColor Yellow
}

Set-Location $PSScriptRoot
Write-Host ""

# Step 2: Stop existing servers
Write-Host "[2/3] Stopping existing servers..." -ForegroundColor Yellow

$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($port8000) {
    $processId = $port8000.OwningProcess
    Write-Host "  Stopping backend on port 8000" -ForegroundColor Gray
    Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

$port3000 = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
if ($port3000) {
    $processId = $port3000.OwningProcess
    Write-Host "  Stopping frontend on port 3000" -ForegroundColor Gray
    Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

$port3001 = Get-NetTCPConnection -LocalPort 3001 -ErrorAction SilentlyContinue
if ($port3001) {
    $processId = $port3001.OwningProcess
    Write-Host "  Stopping frontend on port 3001" -ForegroundColor Gray
    Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

Write-Host "  ✓ Existing servers stopped" -ForegroundColor Green
Write-Host ""

# Step 3: Start servers
Write-Host "[3/3] Starting servers..." -ForegroundColor Yellow

# Start Backend
Write-Host "  Starting backend server..." -ForegroundColor Cyan
$backendCmd = @"
Set-Location '$PSScriptRoot\backend'
Write-Host '========================================' -ForegroundColor Green
Write-Host 'BACKEND SERVER' -ForegroundColor Green
Write-Host '========================================' -ForegroundColor Green
Write-Host ''
Write-Host 'API URL: http://localhost:8000' -ForegroundColor White
Write-Host 'Docs: http://localhost:8000/docs' -ForegroundColor White
Write-Host ''
.\venv\Scripts\activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"@

$backendProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd -PassThru

Start-Sleep -Seconds 3

# Start Frontend
Write-Host "  Starting frontend server..." -ForegroundColor Cyan
$frontendCmd = @"
Set-Location '$PSScriptRoot\frontend'
Write-Host '========================================' -ForegroundColor Green
Write-Host 'FRONTEND SERVER' -ForegroundColor Green
Write-Host '========================================' -ForegroundColor Green
Write-Host ''
Write-Host 'URL: http://localhost:3000' -ForegroundColor White
Write-Host ''
if (Test-Path 'node_modules') {
    npm run dev
} else {
    Write-Host 'Installing dependencies...' -ForegroundColor Yellow
    npm install
    Write-Host ''
    npm run dev
}
"@

$frontendProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd -PassThru

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✓ Servers Started Successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Access the application:" -ForegroundColor Cyan
Write-Host "  Frontend:  http://localhost:3000" -ForegroundColor White
Write-Host "  Backend:   http://localhost:8000" -ForegroundColor White
Write-Host "  API Docs:  http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "Check the opened terminal windows for server logs" -ForegroundColor Yellow
Write-Host "Press Ctrl+C in each window to stop the servers" -ForegroundColor Gray
Write-Host ""
