# PowerShell script to replace Next.js frontend with React frontend
# Run this from the project root: .\migrate_frontend.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "OmniShield Frontend Migration" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Backup old frontend
Write-Host "[1/5] Backing up old Next.js frontend..." -ForegroundColor Yellow
if (Test-Path "frontend") {
    if (Test-Path "frontend-nextjs-backup") {
        Write-Host "  Removing old backup..." -ForegroundColor Gray
        Remove-Item -Recurse -Force "frontend-nextjs-backup"
    }
    Rename-Item "frontend" "frontend-nextjs-backup"
    Write-Host "  ✓ Old frontend backed up to frontend-nextjs-backup" -ForegroundColor Green
} else {
    Write-Host "  ! No existing frontend folder found" -ForegroundColor Yellow
}

# Step 2: Move React frontend to main location
Write-Host ""
Write-Host "[2/5] Moving React frontend to 'frontend' folder..." -ForegroundColor Yellow
if (Test-Path "frontend-react") {
    Rename-Item "frontend-react" "frontend"
    Write-Host "  ✓ React frontend is now in 'frontend' folder" -ForegroundColor Green
} else {
    Write-Host "  ✗ Error: frontend-react folder not found!" -ForegroundColor Red
    exit 1
}

# Step 3: Clean up documentation files
Write-Host ""
Write-Host "[3/5] Cleaning up documentation..." -ForegroundColor Yellow
$docsToRemove = @(
    "TECH_STACK_UPGRADE.txt",
    "DEPLOYMENT_GUIDE.md"
)
foreach ($doc in $docsToRemove) {
    if (Test-Path $doc) {
        # Don't actually remove, just note them
        Write-Host "  - Keeping: $doc" -ForegroundColor Gray
    }
}

# Step 4: Verify frontend structure
Write-Host ""
Write-Host "[4/5] Verifying frontend structure..." -ForegroundColor Yellow
$requiredFiles = @(
    "frontend\package.json",
    "frontend\vite.config.ts",
    "frontend\index.html",
    "frontend\src\main.tsx",
    "frontend\src\App.tsx"
)
$allFilesExist = $true
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "  ✓ $file" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Missing: $file" -ForegroundColor Red
        $allFilesExist = $false
    }
}

if (-not $allFilesExist) {
    Write-Host ""
    Write-Host "  ✗ Some required files are missing!" -ForegroundColor Red
    exit 1
}

# Step 5: Summary
Write-Host ""
Write-Host "[5/5] Migration Summary" -ForegroundColor Yellow
Write-Host "  ✓ Old Next.js frontend -> frontend-nextjs-backup" -ForegroundColor Green
Write-Host "  ✓ New React frontend -> frontend" -ForegroundColor Green
Write-Host "  ✓ All required files verified" -ForegroundColor Green
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Migration Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. cd frontend" -ForegroundColor White
Write-Host "  2. npm install" -ForegroundColor White
Write-Host "  3. npm run dev" -ForegroundColor White
Write-Host ""
Write-Host "Backend:" -ForegroundColor Cyan
Write-Host "  1. cd backend" -ForegroundColor White
Write-Host "  2. python -m venv venv" -ForegroundColor White
Write-Host "  3. .\venv\Scripts\activate" -ForegroundColor White
Write-Host "  4. pip install -r requirements.txt" -ForegroundColor White
Write-Host "  5. uvicorn app.main:app --reload" -ForegroundColor White
Write-Host ""
