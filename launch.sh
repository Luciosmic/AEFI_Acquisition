#!/bin/bash
# Launch script for AEFI Acquisition Interface
# Uses uv to run the application in the managed environment
cd "$(dirname "$0")"

# Ensure environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment with uv..."
    uv venv
    uv pip install -r AEFI_Acquisition/requirements.txt -r visualize_cube/requirements.txt
    uv pip install PySide6 "PySide6-QtAds"
fi

# Run with uv (uses existing .venv)
uv run --no-project python main.py
