@echo off
setlocal
cd /d %~dp0

REM Check if uv is installed
where uv >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Error: 'uv' is not installed or not in PATH.
    pause
    exit /b 1
)

REM Ensure environment is synced
if not exist .venv (
    echo Creating virtual environment and installing dependencies...
    uv sync
)

echo Starting AEFI Acquisition Interface...
uv run python src/main.py

if %ERRORLEVEL% neq 0 (
    echo Application exited with error code %ERRORLEVEL%
    pause
)

