"""Le raccord de sys.path : `interface` vient de src/, jamais du dossier du module, même lancé comme script."""

import os
import subprocess
import sys
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parents[2]
EXTERNAL_MODULES = MODULE_DIR.parent
SRC_DIR = EXTERNAL_MODULES.parent / "src"

_PROBE = """
import sys
sys.path.insert(0, {module_dir!r})  # what running a script of the module does
sys.path.insert(0, {external_modules!r})
from aefi_post_processor_module.aefi_acquisition_upstream import upstream_objects
import interface
print(interface.__file__)
print(upstream_objects.WindowsCarrier.__module__)
"""


def test_interface_resolves_to_src_even_when_the_module_folder_heads_sys_path():
    probe = _PROBE.format(module_dir=str(MODULE_DIR), external_modules=str(EXTERNAL_MODULES))

    result = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True, timeout=120,
                            env={**os.environ, "QT_QPA_PLATFORM": "offscreen", "PYTHONPATH": ""})

    assert result.returncode == 0, result.stderr
    interface_file, carrier_module = result.stdout.splitlines()
    assert Path(interface_file).resolve().is_relative_to(SRC_DIR.resolve())
    assert carrier_module == "interface.widgets.carrier.windows_carrier"
