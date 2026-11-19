"""Lancement de `composition_root.py` dans un processus neuf, Qt hors écran : la fenêtre s'ouvre, `import interface` vient de src/."""

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import h5py

MODULE_DIR = Path(__file__).resolve().parents[1]
COMPOSITION_ROOT = MODULE_DIR / "composition_root.py"
LAUNCH_TIMEOUT_S = 60
BATCH = MODULE_DIR / "_tests" / "synthetic_scans_data_repository" / "batch_20260123_201635"


def make_export(tmp_path, names=("20261112_stepScan_baseline",)):
    """An export folder holding one acquisition per name, each with a real synthetic scan file."""
    export = tmp_path / "export"
    export.mkdir(exist_ok=True)
    for name in names:
        folder = export / name
        folder.mkdir()
        shutil.copy(BATCH / "scan_001_baseline.csv", folder / f"{name}_aefi.csv")
    return export


def launch(tmp_path, *extra_args):
    """Run composition_root.py on the export folder; wait for `window.shown`; stop the process. Returns (journal, output)."""
    export = tmp_path / "export"
    export.mkdir(exist_ok=True)
    log_file = tmp_path / "post_processor.log"
    command = [
        sys.executable, str(COMPOSITION_ROOT), "--repo-path", str(export),
        "--log-file", str(log_file), "--layout-file", str(tmp_path / "layout.dat"), *extra_args,
    ]
    # The output goes to a file, not a pipe: a pipe read only at the end fills up and blocks the process.
    output_file = tmp_path / "output.txt"
    output_stream = open(output_file, "w", encoding="utf-8")
    process = subprocess.Popen(
        command, cwd=tmp_path, stdout=output_stream, stderr=subprocess.STDOUT, text=True,
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
            process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        output_stream.close()
    output = output_file.read_text(encoding="utf-8", errors="replace")
    return (log_file.read_text(encoding="utf-8") if log_file.exists() else journal), output


def test_composition_root_opens_the_window_and_says_so_in_the_journal(tmp_path):
    journal, output = launch(tmp_path)

    assert "window.shown" in journal, output
    assert "Traceback" not in output


def test_the_window_opens_on_an_export_and_lists_its_acquisitions_without_touching_a_file(tmp_path):
    export = make_export(tmp_path, ("20261112_stepScan_baseline", "20261113_flyScan_other"))
    before = sorted((str(p), p.stat().st_mtime) for p in export.rglob("*"))

    journal, output = launch(tmp_path)

    assert "window.shown" in journal, output
    assert "acquisitions.shown" in journal and "count=2" in journal
    assert sorted((str(p), p.stat().st_mtime) for p in export.rglob("*")) == before


def files_with_dates(folder):
    return sorted((str(p), p.stat().st_mtime_ns) for p in folder.rglob("*"))


def test_the_launch_computes_nothing_and_the_journal_says_the_acquisition_is_to_recompute(tmp_path):
    name = "20261112_stepScan_baseline"
    export = make_export(tmp_path, (name,))
    before = files_with_dates(export)

    journal, output = launch(tmp_path)

    assert "window.shown" in journal, output
    assert f"acquisition.state scan={name} state=à recalculer detail=jamais traitée" in journal
    assert "scan.processing" not in journal
    assert files_with_dates(export) == before
    assert not list(export.rglob("*.h5"))


def test_with_force_the_launch_processes_every_acquisition_before_the_window_shows(tmp_path):
    name = "20261112_stepScan_baseline"
    export = make_export(tmp_path, (name,))

    journal, output = launch(tmp_path, "--force")

    assert "window.shown" in journal, output
    assert f"scan.processed scan={name}" in journal
    with h5py.File(export / name / f"{name}.h5", "r") as steps_file:
        assert list(steps_file.keys()) == ["amplitude_subtracted", "interpolated", "phase_calibrated", "preprocessed", "raw_scan", "rotated_frame"]
    assert f"acquisition.state scan={name} state=traitée" in journal


def test_the_window_shows_the_acquisition_parameters_panel_among_its_panels(tmp_path):
    make_export(tmp_path)

    journal, output = launch(tmp_path)

    assert "window.shown" in journal, output
    shown = next(line for line in journal.splitlines() if "window.shown" in line)
    assert "'acquisition_parameters'" in shown
