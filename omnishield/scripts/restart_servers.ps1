# PowerShell script to RESTART both servers (kills existing and starts new ones)
# Run from project root: .\restart_servers.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "OmniShield - Restarting Servers" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Kill existing processes on ports 8000 and 3000/3001
Write-Host "Stopping existing servers..." -ForegroundColor Yellow

# Find and kill process on port 8000 (Backend)
$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($port8000) {
    $processId = $port8000.OwningProcess
    Write-Host "  Stopping backend on port 8000 (PID: $processId)" -ForegroundColor Gray
    Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

# Find and kill process on port 3000 (Frontend)
$port3000 = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
if ($port3000) {
    $processId = $port3000.OwningProcess
    Write-Host "  Stopping frontend on port 3000 (PID: $processId)" -ForegroundColor Gray
    Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

# Find and kill process on port 3001 (Frontend fallback)
$port3001 = Get-NetTCPConnection -LocalPort 3001 -ErrorAction SilentlyContinue
if ($port3001) {
    $processId = $port3001.OwningProcess
    Write-Host "  Stopping frontend on port 3001 (PID: $processId)" -ForegroundColor Gray
    Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

Write-Host "✓ Existing servers stopped" -ForegroundColor Green
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
Write-Host 'CORS Configuration: Allowing all origins (*)' -ForegroundColor Yellow
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

Start-Sleep -Seconds 3

# Start Frontend
Write-Host ""
Write-Host "[2/2] Starting Frontend Server..." -ForegroundColor Cyan
Write-Host "  → http://localhost:3000 (or 3001 if 3000 is busy)" -ForegroundColor Gray

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
Write-Host "Servers Restarted!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "✓ CORS Fix Applied - Backend now accepts all origins" -ForegroundColor Green
Write-Host ""
Write-Host "URLs:" -ForegroundColor Cyan
Write-Host "  Frontend:  http://localhost:3000 (or 3001)" -ForegroundColor White
Write-Host "  Backend:   http://localhost:8000" -ForegroundColor White
Write-Host "  API Docs:  http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C in each terminal to stop servers" -ForegroundColor Yellow
Write-Host ""
