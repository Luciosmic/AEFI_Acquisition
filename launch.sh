#!/bin/bash
# Launch script for AEFI Acquisition Interface
# Uses uv to run the application in the managed environment
cd "$(dirname "$0")"

# Run with uv (automatically manages .venv based on pyproject.toml)
uv run python src/main.py
