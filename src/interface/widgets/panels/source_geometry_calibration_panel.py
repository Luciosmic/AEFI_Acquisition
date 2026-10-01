"""
Source Geometry Calibration Panel

Content widget for the 4-sphere source geometry calibration — a tab of
CalibrationPanel, not its own dock. Entry is in millimeters (an operator
reads a caliper in mm, not scientific-notation meters); converted to meters
before emitting.
"""

from typing import Optional

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGroupBox,
    QFormLayout,
    QDoubleSpinBox,
    QPushButton,
    QLabel,
)
from PySide6.QtCore import Signal

_SPHERE_LABELS = ("S1", "S2", "S3", "S4")
_DISTANCE_LABELS = ("D_S1_S2", "D_S3_S4", "D_S1_S3", "D_S1_S4", "D_S2_S3", "D_S2_S4")


class SourceGeometryCalibrationPanel(QWidget):
    """Record a source geometry calibration entry (caliper measurements)
    and display the last one recorded."""

    save_calibration_requested = Signal(list, list)  # sphere_diameters_m, pairwise_distances_ext_m

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        grp_diameters = QGroupBox("Diamètres des sphères (phi_i)")
        l_diameters = QFormLayout(grp_diameters)
        self.spin_diameters = {label: self._create_length_spinbox() for label in _SPHERE_LABELS}
        for label in _SPHERE_LABELS:
            l_diameters.addRow(f"{label} (mm):", self.spin_diameters[label])
        layout.addWidget(grp_diameters)

        grp_distances = QGroupBox("Distances extrémité-à-extrémité (D_ij)")
        l_distances = QFormLayout(grp_distances)
        self.spin_distances = {label: self._create_length_spinbox() for label in _DISTANCE_LABELS}
        for label in _DISTANCE_LABELS:
            l_distances.addRow(f"{label} (mm):", self.spin_distances[label])
        layout.addWidget(grp_distances)

        self.btn_save = QPushButton("Enregistrer calibration")
        self.btn_save.clicked.connect(self._on_save_clicked)
        layout.addWidget(self.btn_save)

        self.lbl_last_calibration = QLabel("Aucune calibration enregistrée")
        self.lbl_last_calibration.setWordWrap(True)
        self.lbl_last_calibration.setStyleSheet("color: #888; font-style: italic;")
        layout.addWidget(self.lbl_last_calibration)

        layout.addStretch()

    def _create_length_spinbox(self) -> QDoubleSpinBox:
        sb = QDoubleSpinBox()
        sb.setRange(0.0, 200.0)
        sb.setSingleStep(0.02)  # vernier resolution
        sb.setDecimals(3)
        sb.setSuffix(" mm")
        return sb

    def _on_save_clicked(self):
        sphere_diameters_m = [self.spin_diameters[label].value() / 1000.0 for label in _SPHERE_LABELS]
        pairwise_distances_ext_m = [
            self.spin_distances[label].value() / 1000.0 for label in _DISTANCE_LABELS
        ]
        self.save_calibration_requested.emit(sphere_diameters_m, pairwise_distances_ext_m)

    def on_latest_calibration_updated(self, dto: Optional[object]) -> None:
        if dto is None:
            self.lbl_last_calibration.setText("Aucune calibration enregistrée")
            return
        recorded_at = dto.recorded_at.strftime("%Y-%m-%d %H:%M")
        diameters_str = "  ".join(
            f"{label}={v * 1000:.3f}mm" for label, v in zip(_SPHERE_LABELS, dto.sphere_diameters_m)
        )
        distances_str = "  ".join(
            f"{label}={v * 1000:.3f}mm" for label, v in zip(_DISTANCE_LABELS, dto.pairwise_distances_ext_m)
        )
        uncertainty_mm = dto.sphere_diameters_uncertainty_m[0] * 1000
        self.lbl_last_calibration.setText(
            f"{diameters_str}\n{distances_str}\n"
            f"— calibré le {recorded_at} (±{uncertainty_mm:.4f}mm, k={dto.k:g})"
        )
