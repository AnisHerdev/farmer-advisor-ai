# setup_env.ps1 - Environment Setup Script for Farmer Advisor
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "  Farmer Advisor: Initializing Python 3.10 Environment    " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green

if (-not (Test-Path ".venv")) {
    Write-Host "[1/3] Creating Python 3.10 virtual environment in .venv..." -ForegroundColor Cyan
    py -3.10 -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to create .venv with py -3.10. Trying fallback 'python -m venv .venv'..." -ForegroundColor Yellow
        python -m venv .venv
    }
} else {
    Write-Host "[1/3] Virtual environment (.venv) already exists." -ForegroundColor Cyan
}

Write-Host "[2/3] Upgrading pip..." -ForegroundColor Cyan
.\.venv\Scripts\python.exe -m pip install --upgrade pip

Write-Host "[3/3] Installing Python dependencies from requirements.txt..." -ForegroundColor Cyan
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

Write-Host "==========================================================" -ForegroundColor Green
Write-Host "  Setup completed successfully!                           " -ForegroundColor Green
Write-Host "  Run 'npm run dev' to launch Frontend & Backend.        " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
