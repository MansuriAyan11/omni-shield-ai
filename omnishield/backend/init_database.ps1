# Initialize database tables
Write-Host "Initializing database..." -ForegroundColor Cyan

# Activate virtual environment
if (Test-Path "venv\Scripts\activate.ps1") {
    .\venv\Scripts\activate
    Write-Host "✓ Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "✗ Virtual environment not found!" -ForegroundColor Red
    exit 1
}

# Create tables
Write-Host "Creating database tables..." -ForegroundColor Yellow
python create_tables.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Database initialized successfully!" -ForegroundColor Green
    
    # Check if database file was created
    if (Test-Path "moderation.db") {
        $dbSize = (Get-Item "moderation.db").Length
        Write-Host "✓ Database file created: moderation.db ($dbSize bytes)" -ForegroundColor Green
    }
} else {
    Write-Host "✗ Database initialization failed!" -ForegroundColor Red
}
