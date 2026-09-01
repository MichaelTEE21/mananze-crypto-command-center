# MANANZE CRYPTO COMMAND CENTER
$ErrorActionPreference = "Stop"
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  MANANZE CRYPTO COMMAND CENTER" -ForegroundColor Green
Write-Host "  The OS for a crypto researcher" -ForegroundColor DarkGray
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Host "Please tell MANANZE." -ForegroundColor Red
    Write-Host "Python was not found on PATH." -ForegroundColor Yellow
    exit 1
}

Set-Location $PSScriptRoot
if (-not (Test-Path ".venv")) {
    Write-Host "Creating .venv ..." -ForegroundColor DarkGray
    python -m venv .venv
}
& .\.venv\Scripts\Activate.ps1
pip install -q -r requirements.txt
if ((Test-Path ".env.example") -and -not (Test-Path ".env")) {
    Copy-Item .env.example .env
}
Write-Host "Launching on http://localhost:8501 ..." -ForegroundColor Green
streamlit run app.py --server.port 8501
