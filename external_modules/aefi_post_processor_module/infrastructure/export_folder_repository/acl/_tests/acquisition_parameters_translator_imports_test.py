import os
import subprocess
import sys
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parents[4]
EXTERNAL_MODULES = MODULE_DIR.parent


def test_le_traducteur_se_charge_sans_qt_en_empruntant_la_convention_a_l_acquisition():
    """Le câblage sans Qt importe le traducteur : l'emprunt de `RotationConvention` ne doit pas tirer PySide6."""
    code = (
        "import sys\n"
        "from aefi_post_processor_module.infrastructure.export_folder_repository.acl import acquisition_parameters_translator as t\n"
        "from aefi_post_processor_module.aefi_acquisition_upstream.upstream_calibration import RotationConvention\n"
        "import domain.test_bench_calibration.value_objects.rotation_convention.rotation_convention as source\n"
        "assert RotationConvention is source.RotationConvention\n"
        "assert not any(name.split('.')[0] == 'PySide6' for name in sys.modules), 'PySide6 charge'\n"
        "print('ok')\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, timeout=60,
        env={**os.environ, "PYTHONPATH": str(EXTERNAL_MODULES)}, cwd=str(MODULE_DIR),
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ok"
