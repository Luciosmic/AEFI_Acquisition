"""
Sensor Calibration Panel

Tab of CalibrationPanel to record and review the AEFI sensor calibration:
the mounting angles P of the mounted sensor (brings the sensor from the
sources frame to its current mounting; measurement E_sensor = Pᵀ·E_sources;
correction E_sources = P·E_sensor), tuned live by trial and error (applied
without being recorded). Also shows the mounting currently applied to sensor
readings and launches the 3D sensor visualizer. Definition of the
frames and of P: domain/calibration/value_objects/rotation_convention/
rotation_convention_intention.md.
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
    QLineEdit,
)
from PySide6.QtCore import Signal

_PROCEDURE_TEXT = (
    "Angles de montage : P = Rx(θx)·Ry(θy)·Rz(θz) amène le capteur, aligné sur le repère sources, "
    "jusqu'à son montage actuel (axes sources fixes, rotations appliquées Z puis Y puis X).\n"
    "Le capteur mesure E_sensor = Pᵀ·E_sources. « Apply Rotation » (Continuous Reading) et l'export "
    "appliquent la transformation transposée pour revenir au repère sources : E_sources = P·E_sensor.\n"
    "Saisir les angles de montage tels quels, sans les inverser : l'inversion est faite par le logiciel.\n"
    "Réglage par tâtonnement (\"Apply Rotation\" activé, chaque modification s'applique en direct) :\n"
    "1) Excitation selon X : E_x^sources maximal, E_y^sources et E_z^sources minimaux.\n"
    "2) Excitation selon Y : E_y^sources maximal, E_x^sources et E_z^sources minimaux.\n"
    "« Reset to Default » repart des angles idéaux ; « Enregistrer calibration » fige les angles."
)


class SensorCalibrationPanel(QWidget):
    """Record the mounting angles of the mounted sensor and display the last
    ones recorded for this mounting and source geometry. The sensor itself
    (name, transduction gain) is declared and mounted in the 'Capteur' tab."""

    # theta_x, theta_y, theta_z
    save_calibration_requested = Signal(float, float, float)
    launch_visualizer_requested = Signal()
    # theta_x, theta_y, theta_z — live trial, not recorded
    trial_rotation_requested = Signal(float, float, float)
    reset_to_default_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        grp_procedure = QGroupBox("Procédure")
        l_procedure = QVBoxLayout(grp_procedure)
        lbl_procedure = QLabel(_PROCEDURE_TEXT)
        lbl_procedure.setWordWrap(True)
        l_procedure.addWidget(lbl_procedure)
        layout.addWidget(grp_procedure)

        grp_angles = QGroupBox("Angles de montage du capteur (repère sources → montage actuel)")
        l_angles = QFormLayout(grp_angles)
        self.spin_theta_x = self._create_angle_spinbox()
        self.spin_theta_y = self._create_angle_spinbox()
        self.spin_theta_z = self._create_angle_spinbox()
        l_angles.addRow("Theta X (deg):", self.spin_theta_x)
        l_angles.addRow("Theta Y (deg):", self.spin_theta_y)
        l_angles.addRow("Theta Z (deg):", self.spin_theta_z)
        for spin in (self.spin_theta_x, self.spin_theta_y, self.spin_theta_z):
            spin.valueChanged.connect(self._on_angle_changed)
        layout.addWidget(grp_angles)

        self.btn_reset_to_default = QPushButton("Reset to Default")
        self.btn_reset_to_default.clicked.connect(self.reset_to_default_requested.emit)
        layout.addWidget(self.btn_reset_to_default)

        self.btn_auto_calibration = QPushButton("Calibration automatique")
        self.btn_auto_calibration.setEnabled(False)
        self.btn_auto_calibration.setToolTip(
            "À venir : service de calibration automatique (ajustement des angles sur le signal selon le même critère)."
        )
        layout.addWidget(self.btn_auto_calibration)

        self.btn_save = QPushButton("Enregistrer calibration")
        self.btn_save.clicked.connect(self._on_save_clicked)
        layout.addWidget(self.btn_save)

        self.lbl_status = QLabel()
        self.lbl_status.setWordWrap(True)
        layout.addWidget(self.lbl_status)

        self.lbl_last_calibration = QLabel("Aucune calibration enregistrée pour ce montage du capteur")
        self.lbl_last_calibration.setWordWrap(True)
        self.lbl_last_calibration.setStyleSheet("color: #888; font-style: italic;")
        layout.addWidget(self.lbl_last_calibration)

        self.lbl_active_rotation = QLabel("Montage actif : —")
        self.lbl_active_rotation.setWordWrap(True)
        self.lbl_active_rotation.setToolTip(
            "Angles de montage P appliqués ; les mesures sont ramenées dans le repère sources par E_sources = P·E_sensor (Continuous Reading, \"Apply Rotation\")."
        )
        layout.addWidget(self.lbl_active_rotation)

        self.btn_launch_visualizer = QPushButton("Lancer le visualiseur 3D")
        self.btn_launch_visualizer.clicked.connect(self.launch_visualizer_requested.emit)
        layout.addWidget(self.btn_launch_visualizer)

        layout.addStretch()

    def _create_angle_spinbox(self) -> QDoubleSpinBox:
        sb = QDoubleSpinBox()
        sb.setRange(-180.0, 180.0)
        sb.setSingleStep(0.1)
        sb.setDecimals(2)
        sb.setSuffix(" °")
        return sb

    def _on_angle_changed(self, _value: float) -> None:
        self.trial_rotation_requested.emit(
            self.spin_theta_x.value(),
            self.spin_theta_y.value(),
            self.spin_theta_z.value(),
        )

    def _on_save_clicked(self):
        self.save_calibration_requested.emit(
            self.spin_theta_x.value(),
            self.spin_theta_y.value(),
            self.spin_theta_z.value(),
        )

    def set_status_message(self, message: str) -> None:
        """Presenter feedback — red for "Erreur: ..." (e.g. no sensor mounted)."""
        self.lbl_status.setStyleSheet("color: #c62828;" if message.startswith("Erreur") else "color: #888;")
        self.lbl_status.setText(message)

    def on_latest_calibration_updated(self, dto: Optional[object]) -> None:
        if dto is None:
            self.lbl_last_calibration.setText(
                "Aucune calibration enregistrée pour ce montage du capteur et cette géométrie source"
            )
            return
        recorded_at = dto.recorded_at.strftime("%Y-%m-%d %H:%M")
        self.lbl_last_calibration.setText(
            f"theta_x={dto.theta_x_degrees:.2f}°  theta_y={dto.theta_y_degrees:.2f}°  "
            f"theta_z={dto.theta_z_degrees:.2f}°  — calibré le {recorded_at}"
        )

    def on_active_rotation_updated(self, dto: object) -> None:
        # Mirror the active angles in the spinboxes without starting a new trial.
        for spin, value in (
            (self.spin_theta_x, dto.theta_x_degrees),
            (self.spin_theta_y, dto.theta_y_degrees),
            (self.spin_theta_z, dto.theta_z_degrees),
        ):
            spin.blockSignals(True)
            spin.setValue(value)
            spin.blockSignals(False)
        angles = (
            f"θx={dto.theta_x_degrees:.2f}°  θy={dto.theta_y_degrees:.2f}°  θz={dto.theta_z_degrees:.2f}°"
        )
        if dto.is_trial:
            origin = "essai en cours (non enregistré)"
        elif dto.is_calibrated:
            origin = f"calibrée le {dto.recorded_at.strftime('%Y-%m-%d %H:%M')}"
        else:
            origin = "valeurs idéales par défaut (aucune calibration pour cette géométrie)"
        self.lbl_active_rotation.setText(f"Montage actif : {angles} — {origin}")
