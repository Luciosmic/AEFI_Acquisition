import os
from datetime import datetime, timezone
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from interface.widgets.panels.source_geometry_calibration_panel import SourceGeometryCalibrationPanel

_DIAMETERS_M = (0.0196, 0.0196, 0.0195, 0.0195)
_DISTANCES_M = (0.11142, 0.10908, 0.08436, 0.08352, 0.08230, 0.08450)


def _panel():
    QApplication.instance() or QApplication([])
    panel = SourceGeometryCalibrationPanel()
    edits = []
    panel.measurements_edited.connect(lambda d, D: edits.append((d, D)))
    return panel, edits


def test_latest_calibration_loads_the_form_and_asks_for_one_preview():
    panel, edits = _panel()

    panel.on_latest_calibration_updated(SimpleNamespace(
        sphere_diameters_m=_DIAMETERS_M, pairwise_distances_ext_m=_DISTANCES_M,
        sphere_diameters_uncertainty_m=(1.15e-5,) * 4, k=2.0, recorded_at=datetime.now(timezone.utc),
    ))

    assert len(edits) == 1
    diameters, distances = edits[0]
    assert [round(v, 6) for v in diameters] == list(_DIAMETERS_M)
    assert [round(v, 6) for v in distances] == list(_DISTANCES_M)


def test_editing_one_reading_asks_for_a_preview():
    panel, edits = _panel()

    panel.spin_distances["D_S1_S3"].setValue(84.40)

    assert edits[-1][1][2] == 0.0844


def test_preview_and_rejection_render():
    panel, _ = _panel()
    half = 0.032
    corners = ((-half, half), (half, -half), (half, half), (-half, -half))

    panel.on_source_frame_preview_updated(SimpleNamespace(
        sphere_positions_m=corners, sphere_radii_m=(0.0098,) * 4,
        best_fit_square_positions_m=corners, best_fit_square_side_m=0.064,
        square_residuals_m=((0.0, 0.0),) * 4, square_rms_residual_m=0.0,
        distance_residuals_m=(0.0,) * 6,
    ))
    assert "Écart au carré" in panel.lbl_preview.text()

    panel.on_source_frame_preview_rejected("D_S1_S2 overlap")
    assert "D_S1_S2 overlap" in panel.lbl_preview.text()
