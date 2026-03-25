@echo off
REM Script de lancement pour sync_to_cloud.py avec uv run
cd /d %~dp0
uv run sync_to_cloud.py
if %ERRORLEVEL% neq 0 (
    pause
)
