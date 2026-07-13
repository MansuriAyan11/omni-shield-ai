# Complete setup and start script for OmniShield
# This script will:
# 1. Migrate frontend from Next.js to React
# 2. Install all dependencies
# 3. Setup database
# 4. Start both servers

param(
    [switch]$SkipMigration,
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "╔════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   OmniShield - Complete Setup          ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ============================================
# STEP 1: Frontend Migration
# ============================================
if (-not $SkipMigration) {
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
    Write-Host "STEP 1: Frontend Migration" -ForegroundColor Yellow
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
    Write-Host ""
    
    if (Test-Path "frontend") {
        $response = Read-Host "Frontend folder exists. Replace with React version? (y/n)"
        if ($response -eq "y") {
            Write-Host "  → Backing up old frontend..." -ForegroundColor Gray
            if (Test-Path "frontend-nextjs-backup") {
                Remove-Item -Recurse -Force "frontend-nextjs-backup"
            }
            Rename-Item "frontend" "frontend-nextjs-backup"
            Write-Host "  ✓ Backed up to frontend-nextjs-backup" -ForegroundColor Green
        } else {
            Write-Host "  ! Keeping existing frontend" -ForegroundColor Yellow
            $SkipMigration = $true
        }
    }
    
    if (-not $SkipMigration -and (Test-Path "frontend-react")) {
        Write-Host "  → Moving React frontend to main location..." -ForegroundColor Gray
        Rename-Item "frontend-react" "frontend"
        Write-Host "  ✓ React frontend is now active" -ForegroundColor Green
    }
    
    Write-Host ""
}

# ============================================
# STEP 2: Backend Setup
# ============================================
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
Write-Host "STEP 2: Backend Setup" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
Write-Host ""

Set-Location backend

# Check Python
Write-Host "  → Checking Python..." -ForegroundColor Gray
try {
    $pythonVersion = python --version
    Write-Host "  ✓ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Python not found! Please install Python 3.11+" -ForegroundColor Red
    exit 1
}

# Create virtual environment
if (-not (Test-Path "venv")) {
    Write-Host "  → Creating virtual environment..." -ForegroundColor Gray
    python -m venv venv
    Write-Host "  ✓ Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "  ✓ Virtual environment exists" -ForegroundColor Green
}

# Install dependencies
if (-not $SkipInstall) {
    Write-Host "  → Installing Python dependencies..." -ForegroundColor Gray
    Write-Host "    (This may take a few minutes...)" -ForegroundColor Gray
    .\venv\Scripts\activate
    pip install --upgrade pip
    pip install -r requirements.txt
    Write-Host "  ✓ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "  ! Skipping dependency installation" -ForegroundColor Yellow
}

# Setup database
Write-Host "  → Setting up database..." -ForegroundColor Gray
.\venv\Scripts\activate
python create_tables.py
Write-Host "  ✓ Database tables created" -ForegroundColor Green

Set-Location ..
Write-Host ""

# ============================================
# STEP 3: Frontend Setup
# ============================================
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
Write-Host "STEP 3: Frontend Setup" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
Write-Host ""

Set-Location frontend

# Check Node.js
Write-Host "  → Checking Node.js..." -ForegroundColor Gray
try {
    $nodeVersion = node --version
    Write-Host "  ✓ Node.js $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Node.js not found! Please install Node.js 18+" -ForegroundColor Red
    exit 1
}

# Create .env file
if (-not (Test-Path ".env")) {
    Write-Host "  → Creating .env file..." -ForegroundColor Gray
    Copy-Item ".env.example" ".env"
    Write-Host "  ✓ .env file created" -ForegroundColor Green
} else {
    Write-Host "  ✓ .env file exists" -ForegroundColor Green
}

# Install dependencies
if (-not $SkipInstall) {
    Write-Host "  → Installing Node.js dependencies..." -ForegroundColor Gray
    Write-Host "    (This may take a few minutes...)" -ForegroundColor Gray
    npm install
    Write-Host "  ✓ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "  ! Skipping dependency installation" -ForegroundColor Yellow
}

Set-Location ..
Write-Host ""

# ============================================
# STEP 4: Environment Check
# ============================================
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
Write-Host "STEP 4: Environment Check" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
Write-Host ""

# Check backend .env
if (-not (Test-Path "backend\.env")) {
    Write-Host "  ⚠ Backend .env file not found" -ForegroundColor Yellow
    Write-Host "    Copying from .env.example..." -ForegroundColor Gray
    Copy-Item ".env.example" "backend\.env"
    Write-Host "  ✓ Created backend\.env" -ForegroundColor Green
} else {
    Write-Host "  ✓ Backend .env configured" -ForegroundColor Green
}

# Check frontend .env
if (-not (Test-Path "frontend\.env")) {
    Write-Host "  ⚠ Frontend .env file not found" -ForegroundColor Yellow
    Write-Host "    Using default values..." -ForegroundColor Gray
} else {
    Write-Host "  ✓ Frontend .env configured" -ForegroundColor Green
}

Write-Host ""

# ============================================
# STEP 5: Start Servers
# ============================================
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
Write-Host "STEP 5: Starting Servers" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
Write-Host ""

$response = Read-Host "Start both servers now? (y/n)"
if ($response -eq "y") {
    Write-Host ""
    Write-Host "  → Starting Backend (Port 8000)..." -ForegroundColor Cyan
    
    Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
Set-Location '$PWD\backend'
`$Host.UI.RawUI.WindowTitle = 'OmniShield - Backend'
Write-Host ''
Write-Host '╔════════════════════════════════════════╗' -ForegroundColor Green
Write-Host '║      BACKEND SERVER - PORT 8000        ║' -ForegroundColor Green
Write-Host '╚════════════════════════════════════════╝' -ForegroundColor Green
Write-Host ''
.\venv\Scripts\activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"@

    Start-Sleep -Seconds 2
    
    Write-Host "  → Starting Frontend (Port 3000)..." -ForegroundColor Cyan
    
    Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
Set-Location '$PWD\frontend'
`$Host.UI.RawUI.WindowTitle = 'OmniShield - Frontend'
Write-Host ''
Write-Host '╔════════════════════════════════════════╗' -ForegroundColor Green
Write-Host '║     FRONTEND SERVER - PORT 3000        ║' -ForegroundColor Green
Write-Host '╚════════════════════════════════════════╝' -ForegroundColor Green
Write-Host ''
npm run dev
"@

    Start-Sleep -Seconds 2
    
    Write-Host ""
    Write-Host "╔════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║         SERVERS STARTED! 🚀            ║" -ForegroundColor Green
    Write-Host "╚════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    Write-Host "URLs:" -ForegroundColor Cyan
    Write-Host "  Frontend:  " -NoNewline -ForegroundColor Gray
    Write-Host "http://localhost:3000" -ForegroundColor White
    Write-Host "  Backend:   " -NoNewline -ForegroundColor Gray
    Write-Host "http://localhost:8000" -ForegroundColor White
    Write-Host "  API Docs:  " -NoNewline -ForegroundColor Gray
    Write-Host "http://localhost:8000/docs" -ForegroundColor White
    Write-Host ""
    Write-Host "✓ Setup Complete!" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "Setup complete! To start servers later, run:" -ForegroundColor Cyan
    Write-Host "  .\start_servers.ps1" -ForegroundColor White
    Write-Host ""
}
