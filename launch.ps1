# Launch script for AEFI Acquisition Interface (PowerShell)

Set-Location $PSScriptRoot

# Check if uv is installed
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "Error: 'uv' is not installed or not in PATH." -ForegroundColor Red
    Pause
    exit
}

# Ensure environment is synced
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment and installing dependencies..." -ForegroundColor Cyan
    uv sync
}

Write-Host "Starting AEFI Acquisition Interface..." -ForegroundColor Green
uv run python src/main.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "Application exited with error code $LASTEXITCODE" -ForegroundColor Red
    Pause
}
