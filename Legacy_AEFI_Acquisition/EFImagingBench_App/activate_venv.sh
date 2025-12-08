#!/bin/bash
# Activation script for EFImagingBench virtual environment

echo "🚀 Activating EFImagingBench virtual environment..."
source .venv_efi_imaging_bench/bin/activate

echo "✅ Virtual environment activated!"
echo ""
echo "Python: $(which python3)"
echo "Pip: $(which pip)"
echo ""
echo "Installed packages:"
pip list | grep -E "(PyQt5|pytest|numpy|matplotlib)"
echo ""
echo "To deactivate, run: deactivate"
