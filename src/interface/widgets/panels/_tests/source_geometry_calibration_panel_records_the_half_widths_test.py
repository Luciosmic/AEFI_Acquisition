"""
Panel -> presenter -> service -> JSON registry, offscreen: what the operator
types (the 2026-11-24 compression-mount readings, ±0.25 mm on the distances,
±0.01 mm on the diameters) is what the recorded calibration carries once
read back from disk. No hardware, no window shown.
"""

import math
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from application.test_bench_calibration.source_geometry_calibration_service.source_geometry_calibration_service import (
    SourceGeometryCalibrationService,
)
from infrastructure.in_memory_event_bus.in_memory_event_bus import InMemoryEventBus
from infrastructure.persistence.calibration.real_source_geometry_calibration_repository import (
    RealSourceGeometryCalibrationRepository,
)
from interface.presenters.source_geometry_calibration_presenter import SourceGeometryCalibrationPresenter
from interface.widgets.panels.source_geometry_calibration_panel import SourceGeometryCalibrationPanel

_DISTANCES_MM = {
    "D_S1_S2": 103.020, "D_S3_S4": 103.707, "D_S1_S3": 78.880,
    "D_S1_S4": 79.600, "D_S2_S3": 79.333, "D_S2_S4": 78.860,
}
_DIAMETERS_MM = {"S1": 19.620, "S2": 19.600, "S3": 19.520, "S4": 19.480}


def _wired_panel(storage_path):
    QApplication.instance() or QApplication([])
    event_bus = InMemoryEventBus()
    service = SourceGeometryCalibrationService(
        RealSourceGeometryCalibrationRepository(storage_path=storage_path), event_bus
    )
    presenter = SourceGeometryCalibrationPresenter(service, event_bus)
    panel = SourceGeometryCalibrationPanel()
    panel.save_calibration_requested.connect(presenter.on_save_calibration_requested)
    messages = []
    presenter.status_message.connect(messages.append)
    return panel, presenter, messages


def test_saved_calibration_carries_0_25_mm_on_distances_and_0_01_mm_on_diameters(tmp_path):
    storage_path = tmp_path / "source_geometry_calibration.json"
    panel, presenter, messages = _wired_panel(storage_path)
    for label, value in _DISTANCES_MM.items():
        panel.spin_distances[label].setValue(value)
    for label, value in _DIAMETERS_MM.items():
        panel.spin_diameters[label].setValue(value)
    panel.spin_distance_half_width.setValue(0.25)
    panel.spin_diameter_half_width.setValue(0.01)

    panel.btn_save.click()

    assert messages == ["Calibration enregistrée"]
    (entry,) = RealSourceGeometryCalibrationRepository(storage_path=storage_path).find_all()
    for m, value_mm in zip(entry.pairwise_distances_ext, _DISTANCES_MM.values()):
        assert m.value_m == pytest.approx(value_mm / 1000, abs=1e-12)
        assert m.uniform_half_width_m == pytest.approx(0.00025, rel=1e-12)
        assert m.uncertainty_expanded_m / m.k == pytest.approx(0.00025 / math.sqrt(3), rel=1e-9)
    for m, value_mm in zip(entry.sphere_diameters, _DIAMETERS_MM.values()):
        assert m.value_m == pytest.approx(value_mm / 1000, abs=1e-12)
        assert m.uniform_half_width_m == pytest.approx(0.00001, rel=1e-12)
        assert m.uncertainty_expanded_m / m.k == pytest.approx(0.00001 / math.sqrt(3), rel=1e-9)


def test_default_half_widths_record_the_former_vernier_uncertainty(tmp_path):
    storage_path = tmp_path / "source_geometry_calibration.json"
    panel, _, _ = _wired_panel(storage_path)
    for label, value in _DISTANCES_MM.items():
        panel.spin_distances[label].setValue(value)
    for label, value in _DIAMETERS_MM.items():
        panel.spin_diameters[label].setValue(value)

    panel.btn_save.click()

    (entry,) = RealSourceGeometryCalibrationRepository(storage_path=storage_path).find_all()
    former_u = 0.00002 / (2 * math.sqrt(3))  # from_resolution, 0.02 mm vernier
    for m in (*entry.sphere_diameters, *entry.pairwise_distances_ext):
        assert m.uncertainty_expanded_m / m.k == pytest.approx(former_u, rel=1e-12)
