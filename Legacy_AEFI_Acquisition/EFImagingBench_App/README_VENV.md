# EFImagingBench Application

## Virtual Environment Setup

### Created Environment
- **Name**: `.venv_efi_imaging_bench`
- **Python**: 3.13
- **Location**: `Legacy_AEFI_Acquisition/EFImagingBench_App/`

### Installed Packages
- PyQt5 5.15.11
- pytest 9.0.2
- pytest-qt 4.5.0
- numpy 2.3.5
- matplotlib 3.10.7
- black 25.12.0
- flake8 7.3.0
- mypy 1.19.0

## Activation

### macOS/Linux
```bash
source .venv_efi_imaging_bench/bin/activate
```

Or use the helper script:
```bash
./activate_venv.sh
```

### Deactivation
```bash
deactivate
```

## Running Tests

### Unit Tests (no GUI)
```bash
.venv_efi_imaging_bench/bin/python3 test_data_driven_ui.py
```

### PyQt Tests
```bash
.venv_efi_imaging_bench/bin/pytest src/interface/hardware_configuration_tabs/tests/ -v
```

### Run UI Example
```bash
.venv_efi_imaging_bench/bin/python3 examples/data_driven_ui_example.py
```

## Development

### Code Formatting
```bash
.venv_efi_imaging_bench/bin/black src/
```

### Linting
```bash
.venv_efi_imaging_bench/bin/flake8 src/
```

### Type Checking
```bash
.venv_efi_imaging_bench/bin/mypy src/
```
