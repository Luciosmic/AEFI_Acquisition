"""Lancement de `composition_root.py` dans un processus neuf, Qt hors écran : la fenêtre s'ouvre, `import interface` vient de src/."""

import os
import subprocess
import sys
import time
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parents[1]
COMPOSITION_ROOT = MODULE_DIR / "composition_root.py"
LAUNCH_TIMEOUT_S = 60


def launch(tmp_path, *extra_args):
    """Run composition_root.py on an empty export folder; wait for `window.shown`; stop the process. Returns (journal, output)."""
    export = tmp_path / "export"
    export.mkdir(exist_ok=True)
    log_file = tmp_path / "post_processor.log"
    command = [
        sys.executable, str(COMPOSITION_ROOT), "--repo-path", str(export),
        "--log-file", str(log_file), "--layout-file", str(tmp_path / "layout.dat"), *extra_args,
    ]
    process = subprocess.Popen(
        command, cwd=tmp_path, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        env={**os.environ, "QT_QPA_PLATFORM": "offscreen", "PYTHONPATH": ""},
    )
    deadline = time.monotonic() + LAUNCH_TIMEOUT_S
    journal = ""
    try:
        while time.monotonic() < deadline and process.poll() is None:
            journal = log_file.read_text(encoding="utf-8") if log_file.exists() else ""
            if "window.shown" in journal:
                break
            time.sleep(0.2)
    finally:
        if process.poll() is None:
            process.terminate()
        try:
            output, _ = process.communicate(timeout=20)
        except subprocess.TimeoutExpired:
            process.kill()
            output, _ = process.communicate()
    return (log_file.read_text(encoding="utf-8") if log_file.exists() else journal), output


def test_composition_root_opens_the_window_and_says_so_in_the_journal(tmp_path):
    journal, output = launch(tmp_path)

    assert "window.shown" in journal, output
    assert "Traceback" not in output
