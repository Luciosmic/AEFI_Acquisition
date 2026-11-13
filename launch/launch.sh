#!/bin/bash
# Launch script for AEFI Acquisition Interface
# Uses uv to run the application in the managed environment
cd "$(dirname "$0")/.."

# Le venv vit hors de Dropbox, propre à chaque machine (voir VENV.md).
# Sans cette variable, uv recréerait .venv/ ici, dans Dropbox.
export UV_PROJECT_ENVIRONMENT="${UV_PROJECT_ENVIRONMENT:-$HOME/.venvs/AEFI_Acquisition}"

# Run with uv (manages the venv above based on pyproject.toml)
uv run python src/interface/main.py
