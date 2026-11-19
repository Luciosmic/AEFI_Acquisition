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
        # No parameters file: the folder name gives the type only, never the object.
        assert _cells(acquisitions) == [["—", "inconnue", "pas à pas", "non renseigné", "non renseigné", "à recalculer", "jamais traitée"]]
        assert acquisitions.table.item(0, 0).toolTip() == NAME

        acquisitions.table.selectRow(0)
        acquisitions.process_selection_requested.emit()

        assert _cells(acquisitions)[0][5] == "traitée"
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


def _write_parameters(folder, name):
    import json

    (folder / f"{name}_acquisition-parameters.json").write_text(json.dumps({
        "schema": {"version": "1.4"},
        "provenance": {"activity": {"kind": "step_scan", "started_at": "2026-11-12T20:57:00.050+01:00"}},
        "feature_of_interest": {"description": "bouteille_cristalline"},
        "measurement_chain": {"sensor": {"deployment": {"rotation_applied": {
            "theta_x": {"value": 34.9, "unit": "deg"}, "theta_y": {"value": 45.7, "unit": "deg"},
            "theta_z": {"value": -5.3, "unit": "deg"},
            "convention": {"type": "extrinsic", "order": "ZYX", "direction": "sources_to_sensor"},
            "origin": "calibrated", "applies_to_data": False}}}},
    }), encoding="utf-8")


def test_choosing_an_acquisition_fills_the_parameters_panel_and_changes_no_file(qtbot, tmp_path):
    from PySide6.QtWidgets import QLabel

    export = tmp_path / "export"
    (export / NAME).mkdir(parents=True)
    shutil.copy(BATCH / "scan_001_baseline.csv", export / NAME / f"{NAME}_aefi.csv")
    _write_parameters(export / NAME, NAME)
    before = sorted((str(p), p.stat().st_mtime) for p in export.rglob("*"))
    feedback = FeedbackLogHandler(logging.INFO)
    shell = build_shell(
        feedback, str(tmp_path / "post_processor.log"), str(tmp_path / "layout.dat"), str(export),
        lambda: ProcessingParameters(rotation_angles=(0.0, 0.0, 45.0)), "test",
    )
    qtbot.addWidget(shell.window)
    assert set(shell.window.carrier_view._panels) == {"acquisitions", "acquisition_parameters", "field_map", "logs"}
    acquisitions = shell.window.carrier_view._panels["acquisitions"].widget()
    parameters = shell.window.carrier_view._panels["acquisition_parameters"].widget()
    shell.acquisitions_presenter.refresh()

    acquisitions.table.selectRow(0)

    texts = [label.text() for label in parameters.findChildren(QLabel)]
    assert NAME in texts and "bouteille_cristalline" in texts and "34.9 °" in texts and "45.7 °" in texts and "-5.3 °" in texts
    assert "extrinsic · ZYX · sources_to_sensor" in texts and "1.4" in texts and "ceux de l'acquisition" in texts
    assert sorted((str(p), p.stat().st_mtime) for p in export.rglob("*")) == before

    acquisitions.table.clearSelection()
    assert "Aucune acquisition sélectionnée" in [label.text() for label in parameters.findChildren(QLabel)]
