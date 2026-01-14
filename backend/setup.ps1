# Setup Script for Stock Selection Backend
# This script helps set up the backend environment

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Stock Selection Backend - Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "Checking Python version..." -ForegroundColor Yellow
$pythonVersion = py --version 2>&1
if ($pythonVersion -match "Python 3\.([0-9]+)") {
    $minorVersion = [int]$Matches[1]
    if ($minorVersion -ge 10) {
        Write-Host "[OK] Python version: $pythonVersion" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Python 3.10 or higher required. Found: $pythonVersion" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[ERROR] Python not found or version check failed" -ForegroundColor Red
    exit 1
}

# Create virtual environment
Write-Host ""
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "Virtual environment already exists" -ForegroundColor Yellow
} else {
    py -m venv venv
    Write-Host "[OK] Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host ""
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1
Write-Host "[OK] Virtual environment activated" -ForegroundColor Green

# Upgrade pip
Write-Host ""
Write-Host "Upgrading pip..." -ForegroundColor Yellow
.\venv\Scripts\python.exe -m pip install --upgrade pip --quiet
Write-Host "[OK] pip upgraded" -ForegroundColor Green

# Install dependencies
Write-Host ""
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Error installing dependencies" -ForegroundColor Red
    exit 1
}

# Create necessary directories
Write-Host ""
Write-Host "Creating directories..." -ForegroundColor Yellow
$dirs = @("logs", "output", "data\cache", "data\historical")
foreach ($dir in $dirs) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "[OK] Created $dir/" -ForegroundColor Green
    } else {
        Write-Host "  $dir/ already exists" -ForegroundColor Gray
    }
}

# Create .env file if it doesn't exist
Write-Host ""
Write-Host "Setting up environment file..." -ForegroundColor Yellow
if (!(Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "[OK] Created .env file (please edit with your API keys)" -ForegroundColor Green
} else {
    Write-Host ".env file already exists" -ForegroundColor Gray
}

# Run tests
Write-Host ""
Write-Host "Running tests..." -ForegroundColor Yellow
pytest tests/ -v --tb=short
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] All tests passed" -ForegroundColor Green
} else {
    Write-Host "[WARNING] Some tests failed (this is OK if you don't have test data)" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Edit .env file with your API keys (optional)" -ForegroundColor White
Write-Host "2. Run example: python examples/technical_analysis_example.py" -ForegroundColor White
Write-Host "3. Check output/ directory for results" -ForegroundColor White
Write-Host ""
Write-Host "To activate environment later:" -ForegroundColor Yellow
Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host ""
Write-Host "Happy trading!" -ForegroundColor Cyan

