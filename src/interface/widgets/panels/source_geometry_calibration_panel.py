"""
Source Geometry Calibration Panel

Content widget for the 4-sphere source geometry calibration — a tab of
CalibrationPanel, not its own dock. Entry is in millimeters (an operator
reads a caliper in mm, not scientific-notation meters); converted to meters
before emitting. Every edit emits `measurements_edited`, answered by a live
preview of the reconstructed sphere positions (nothing recorded until Save).
"""

import math
from typing import Optional

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.patches import Circle
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

_SPHERE_LABELS = ("S1", "S2", "S3", "S4")
_SPHERE_QUADRANTS = ("x_neg_y_pos", "x_pos_y_neg", "x_pos_y_pos", "x_neg_y_neg")
_DISTANCE_LABELS = ("D_S1_S2", "D_S3_S4", "D_S1_S3", "D_S1_S4", "D_S2_S3", "D_S2_S4")
# S1<->S2 and S3<->S4 are the diagonals: S1, S3, S2, S4 walks the perimeter
_PERIMETER = (0, 2, 1, 3)
_CALIPER_RESOLUTION_MM = 0.02
_FG = "#DDDDDD"


class SourceGeometryCalibrationPanel(QWidget):
    """Record a source geometry calibration entry (caliper measurements),
    preview the reconstructed sphere positions live, and display the last
    one recorded."""

    save_calibration_requested = Signal(list, list)  # sphere_diameters_m, pairwise_distances_ext_m
    measurements_edited = Signal(list, list)  # sphere_diameters_m, pairwise_distances_ext_m

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        form = QVBoxLayout()
        layout.addLayout(form)

        grp_diameters = QGroupBox("Diamètres des sphères (phi_i)")
        l_diameters = QFormLayout(grp_diameters)
        self.spin_diameters = {label: self._create_length_spinbox() for label in _SPHERE_LABELS}
        for label in _SPHERE_LABELS:
            l_diameters.addRow(f"{label} (mm):", self.spin_diameters[label])
        form.addWidget(grp_diameters)

        grp_distances = QGroupBox("Distances extrémité-à-extrémité (D_ij)")
        l_distances = QFormLayout(grp_distances)
        self.spin_distances = {label: self._create_length_spinbox() for label in _DISTANCE_LABELS}
        for label in _DISTANCE_LABELS:
            l_distances.addRow(f"{label} (mm):", self.spin_distances[label])
        form.addWidget(grp_distances)

        self.btn_save = QPushButton("Enregistrer calibration")
        self.btn_save.clicked.connect(self._on_save_clicked)
        form.addWidget(self.btn_save)

        self.lbl_last_calibration = QLabel("Aucune calibration enregistrée")
        self.lbl_last_calibration.setWordWrap(True)
        self.lbl_last_calibration.setStyleSheet("color: #888; font-style: italic;")
        form.addWidget(self.lbl_last_calibration)
        form.addStretch()

        preview = QVBoxLayout()
        layout.addLayout(preview, stretch=1)
        self.figure = Figure(facecolor="#1E1E1E")
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setMinimumSize(360, 360)
        preview.addWidget(self.canvas, stretch=1)
        self.lbl_preview = QLabel("Aperçu : saisir les mesures")
        self.lbl_preview.setWordWrap(True)
        preview.addWidget(self.lbl_preview)

        for spin in (*self.spin_diameters.values(), *self.spin_distances.values()):
            spin.valueChanged.connect(self._emit_measurements_edited)

    def _create_length_spinbox(self) -> QDoubleSpinBox:
        sb = QDoubleSpinBox()
        sb.setRange(_CALIPER_RESOLUTION_MM, 200.0)  # a 0 mm reading is not a measurement
        sb.setSingleStep(_CALIPER_RESOLUTION_MM)  # vernier resolution
        sb.setDecimals(3)
        sb.setSuffix(" mm")
        return sb

    def _measurements_m(self):
        sphere_diameters_m = [self.spin_diameters[label].value() / 1000.0 for label in _SPHERE_LABELS]
        pairwise_distances_ext_m = [
            self.spin_distances[label].value() / 1000.0 for label in _DISTANCE_LABELS
        ]
        return sphere_diameters_m, pairwise_distances_ext_m

    def _emit_measurements_edited(self, *_):
        self.measurements_edited.emit(*self._measurements_m())

    def _on_save_clicked(self):
        self.save_calibration_requested.emit(*self._measurements_m())

    def on_latest_calibration_updated(self, dto: Optional[object]) -> None:
        if dto is None:
            self.lbl_last_calibration.setText("Aucune calibration enregistrée")
            return
        self._load_measurements(dto.sphere_diameters_m, dto.pairwise_distances_ext_m)
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

    def _load_measurements(self, sphere_diameters_m, pairwise_distances_ext_m) -> None:
        """Start editing from the recorded values; one preview, not one per field."""
        spins = list(self.spin_diameters.values()) + list(self.spin_distances.values())
        for spin, value_m in zip(spins, (*sphere_diameters_m, *pairwise_distances_ext_m)):
            spin.blockSignals(True)
            spin.setValue(value_m * 1000.0)
            spin.blockSignals(False)
        self._emit_measurements_edited()

    def on_source_frame_preview_updated(self, dto) -> None:
        ax = self._reset_axes()
        mm = 1000.0
        for label, quadrant, (x, y), r in zip(
            _SPHERE_LABELS, _SPHERE_QUADRANTS, dto.sphere_positions_m, dto.sphere_radii_m
        ):
            ax.add_patch(Circle((x * mm, y * mm), r * mm, fill=False, edgecolor="#4FC3F7", linewidth=1.5))
            ax.plot(x * mm, y * mm, "o", color="#4FC3F7", markersize=3)
            ax.annotate(f"{label}\n{quadrant}", (x * mm, y * mm), color=_FG, fontsize=8,
                        textcoords="offset points", xytext=(6, 6))
        ax.plot(*self._loop(dto.sphere_positions_m, mm), "-", color="#4FC3F7", label="reconstruit")
        ax.plot(*self._loop(dto.best_fit_square_positions_m, mm), "--", color="#999999",
                label=f"carré ajusté ({dto.best_fit_square_side_m * mm:.2f} mm)")
        ax.axhline(0, color="#444444", linewidth=0.8)
        ax.axvline(0, color="#444444", linewidth=0.8)
        ax.set_title(f"Écart RMS au carré : {dto.square_rms_residual_m * 1e6:.0f} µm", color=_FG, fontsize=10)
        ax.legend(loc="center", fontsize=7)  # every corner holds a sphere, the middle is empty
        ax.relim()
        ax.autoscale_view()
        self.canvas.draw_idle()

        square = "  ".join(
            f"{label} {math.hypot(dx, dy) * 1e6:.0f}µm"
            for label, (dx, dy) in zip(_SPHERE_LABELS, dto.square_residuals_m)
        )
        distances = "  ".join(
            f"{label} {r * 1e6:+.0f}µm" for label, r in zip(_DISTANCE_LABELS, dto.distance_residuals_m)
        )
        self.lbl_preview.setStyleSheet("color: #AAA;")
        self.lbl_preview.setText(
            f"Écart au carré par sphère : {square}\nRésidus de reconstruction : {distances}"
        )

    def on_source_frame_preview_rejected(self, reason: str) -> None:
        self._reset_axes()
        self.canvas.draw_idle()
        self.lbl_preview.setStyleSheet("color: #F44336; font-weight: bold;")
        self.lbl_preview.setText(f"Géométrie impossible : {reason}")

    def _reset_axes(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111, facecolor="#1E1E1E")
        ax.set_aspect("equal")
        ax.set_xlabel("x (mm)", color=_FG)
        ax.set_ylabel("y (mm)", color=_FG)
        ax.tick_params(colors=_FG, labelsize=8)
        ax.grid(True, linestyle=":", color="#333333")
        return ax

    @staticmethod
    def _loop(points, scale):
        ordered = [points[i] for i in _PERIMETER] + [points[_PERIMETER[0]]]
        return [p[0] * scale for p in ordered], [p[1] * scale for p in ordered]
