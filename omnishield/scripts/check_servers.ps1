# Check if servers are running and responsive

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Checking Server Status" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Backend (Port 8000)
Write-Host "[1/2] Checking Backend (Port 8000)..." -ForegroundColor Yellow
$backend8000 = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if ($backend8000) {
    $backendPID = $backend8000.OwningProcess
    $backendProcess = Get-Process -Id $backendPID -ErrorAction SilentlyContinue
    Write-Host "  ✓ Port 8000 is LISTENING" -ForegroundColor Green
    if ($backendProcess) {
        Write-Host "    Process: $($backendProcess.ProcessName) (PID: $backendPID)" -ForegroundColor Gray
    }
    
    # Try to connect
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000" -UseBasicParsing -TimeoutSec 3
        Write-Host "  ✓ Backend is RESPONDING (Status: $($response.StatusCode))" -ForegroundColor Green
        Write-Host "    URL: http://localhost:8000" -ForegroundColor White
        Write-Host "    Docs: http://localhost:8000/docs" -ForegroundColor White
    } catch {
        Write-Host "  ⚠ Port is listening but not responding yet" -ForegroundColor Yellow
        Write-Host "    (Server might still be starting up)" -ForegroundColor Gray
    }
} else {
    Write-Host "  ✗ Backend NOT running on port 8000" -ForegroundColor Red
}

Write-Host ""

# Check Frontend (Port 3000)
Write-Host "[2/2] Checking Frontend (Port 3000)..." -ForegroundColor Yellow
$frontend3000 = Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue
if ($frontend3000) {
    $frontendPID = $frontend3000.OwningProcess
    $frontendProcess = Get-Process -Id $frontendPID -ErrorAction SilentlyContinue
    Write-Host "  ✓ Port 3000 is LISTENING" -ForegroundColor Green
    if ($frontendProcess) {
        Write-Host "    Process: $($frontendProcess.ProcessName) (PID: $frontendPID)" -ForegroundColor Gray
    }
    Write-Host "    URL: http://localhost:3000" -ForegroundColor White
} else {
    Write-Host "  ⚠ Frontend NOT on port 3000, checking 3001..." -ForegroundColor Yellow
    
    # Check Port 3001
    $frontend3001 = Get-NetTCPConnection -LocalPort 3001 -State Listen -ErrorAction SilentlyContinue
    if ($frontend3001) {
        $frontendPID = $frontend3001.OwningProcess
        $frontendProcess = Get-Process -Id $frontendPID -ErrorAction SilentlyContinue
        Write-Host "  ✓ Port 3001 is LISTENING" -ForegroundColor Green
        if ($frontendProcess) {
            Write-Host "    Process: $($frontendProcess.ProcessName) (PID: $frontendPID)" -ForegroundColor Gray
        }
        Write-Host "    URL: http://localhost:3001" -ForegroundColor White
    } else {
        Write-Host "  ✗ Frontend NOT running on port 3000 or 3001" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan

# Show all PowerShell windows (likely server terminals)
$psProcesses = Get-Process powershell -ErrorAction SilentlyContinue
if ($psProcesses) {
    Write-Host ""
    Write-Host "Active PowerShell Processes: $($psProcesses.Count)" -ForegroundColor Yellow
    Write-Host "(Check for terminal windows with server logs)" -ForegroundColor Gray
}

Write-Host ""
