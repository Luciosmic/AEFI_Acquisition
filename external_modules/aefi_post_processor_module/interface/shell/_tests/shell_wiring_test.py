"""La coquille entière en processus, adaptateurs réels, Qt hors écran : lister, traiter, choisir une étape, lire la carte."""

import logging
import os
import shutil
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from ....domain.processing.processing_steps.processing_steps import STEP_NAMES, ProcessingParameters
from ....infrastructure.logging.logging_setup import FeedbackLogHandler
from ..shell_wiring import build_shell

BATCH = Path(__file__).resolve().parents[3] / "_tests" / "synthetic_scans_data_repository" / "batch_20260123_201635"
NAME = "20261112_stepScan_baseline"


def _cells(panel):
    return [[panel.table.item(r, c).text() for c in range(panel.table.columnCount())] for r in range(panel.table.rowCount())]


def test_processing_from_the_panel_then_choosing_a_step_draws_its_map_and_the_balance_reaches_the_logs(qtbot, tmp_path):
    export = tmp_path / "export"
    (export / NAME).mkdir(parents=True)
    shutil.copy(BATCH / "scan_001_baseline.csv", export / NAME / f"{NAME}_aefi.csv")
    feedback = FeedbackLogHandler(logging.INFO)
    root = logging.getLogger()
    root.addHandler(feedback)
    previous_level = root.level
    root.setLevel(logging.INFO)
    try:
        shell = build_shell(
            feedback, str(tmp_path / "post_processor.log"), str(tmp_path / "layout.dat"), str(export),
            lambda: ProcessingParameters(rotation_angles=(0.0, 0.0, 45.0)), "test",
        )
        qtbot.addWidget(shell.window)
        acquisitions = shell.window.carrier_view._panels["acquisitions"].widget()
        field_map = shell.window.carrier_view._panels["field_map"].widget()
        logs = shell.window.carrier_view._panels["logs"].widget()
        shell.acquisitions_presenter.refresh()
        assert _cells(acquisitions) == [[NAME, "pas à pas", "baseline", "à recalculer", "jamais traitée"]]

        acquisitions.table.selectRow(0)
        acquisitions.process_selection_requested.emit()

        assert _cells(acquisitions)[0][3] == "traitée"
        assert [field_map.steps.item(i).text() for i in range(field_map.steps.count())] == [
            f"{i} - {step}" for i, step in enumerate(STEP_NAMES, 1)
        ]
        field_map.steps.setCurrentRow(4)
        assert field_map.plot_layout.count() == 1 and field_map.plot_layout.itemAt(0).widget() is not field_map.placeholder
        assert field_map.rotation_label.text() == "Rotation: [0.00, 0.00, 45.00]"
        assert "sync.finished processed=1 skipped=0 failed=0" in logs.text.toPlainText()
    finally:
        root.removeHandler(feedback)
        root.setLevel(previous_level)
