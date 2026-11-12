"""
Sensor Calibration Panel

Tab of CalibrationPanel to record and review the AEFI sensor calibration:
the mounting angles P of the mounted sensor (brings the sensor from the
sources frame to its current mounting; measurement E_sensor = Pᵀ·E_sources;
correction E_sources = P·E_sensor), tuned live by trial and error (applied
without being recorded). Also shows the mounting currently applied to sensor
readings, in text and in 3D (injected orientation view). Definition of the
frames and of P: domain/test_bench/calibration/value_objects/rotation_convention/
rotation_convention_intention.md.
"""

from typing import Optional

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QGroupBox,
    QFormLayout,
    QDoubleSpinBox,
    QPushButton,
    QLabel,
    QLineEdit,
    QScrollArea,
    QFrame,
)
from PySide6.QtCore import Qt, Signal

from interface.widgets.collapsible_section.collapsible_section import CollapsibleSection

_MANUAL_PROCEDURE_TEXT = (
    "Par tâtonnement, en regardant le signal ramené dans le repère sources :<ol>"
    "<li>Dans l'onglet <i>Capteur</i>, vérifier que le capteur monté est le bon ; dans <i>Géométrie source</i>, "
    "que la géométrie des sphères est celle du banc.</li>"
    "<li>Dans <i>Excitation &amp; Lock-In Detection</i>, régler le niveau d'excitation et choisir le mode "
    "<i>X Direction</i> pour commencer.</li>"
    "<li>Dans <i>AEFI Continuous Reading</i>, lancer <i>Start</i> et activer <i>Apply Rotation</i> : les "
    "signaux affichés sont alors E_sources = P·E_sensor, avec les angles de cet onglet.</li>"
    "<li>Partir de <i>Reset to Default</i> (angles idéaux : le cube repose sur un sommet).</li>"
    "<li>Modifier les angles θx, θy, θz (pas de 0,1°) : chaque changement s'applique en direct, sans être "
    "enregistré. Excitation selon X, chercher E_x maximal avec E_y et E_z minimaux.</li>"
    "<li>Passer le mode d'excitation à <i>Y Direction</i> : E_y doit être maximal avec E_x et E_z minimaux. "
    "Revenir à X, puis à Y, en alternant jusqu'à ce que les deux directions soient satisfaites ensemble "
    "(il n'existe pas de formule : le champ primaire du banc n'est pas uniforme).</li>"
    "<li><i>Enregistrer calibration</i> : fige les angles dans une nouvelle entrée datée, liée au capteur monté "
    "et à la géométrie source. Tant qu'on n'enregistre pas, l'essai n'est qu'un essai.</li></ol>"
)

_CONVENTION_TEXT = (
    "P = Rx(θx)·Ry(θy)·Rz(θz) amène le capteur, aligné sur le repère sources, "
    "jusqu'à son montage actuel (axes sources fixes, rotations appliquées Z puis Y puis X). Le capteur mesure "
    "E_sensor = Pᵀ·E_sources ; « Apply Rotation » et l'export appliquent la transformation transposée : "
    "E_sources = P·E_sensor. Saisir les angles de montage tels quels, sans les inverser : l'inversion est "
    "faite par le logiciel."
)

_AUTOMATIC_TEXT = (
    "Expérimentale : ses angles se sont montrés peu fiables sur le banc, la calibration manuelle fait foi. "
    "Au niveau d'excitation réglé, elle mesure la baseline (excitation "
    "coupée), puis les réponses aux excitations X et Y, calcule les angles qui les alignent au mieux sur "
    "e_x et e_y (moindres carrés), les applique en essai et restaure l'excitation. Elle ne remplace pas "
    "le contrôle visuel de la procédure manuelle : ses angles restent un essai tant qu'ils ne sont pas enregistrés."
)

# Explicit titles, folded by default: the tab stays about the angles, the help is one click away.
_HELP_SECTIONS = (
    ("Comment calibrer le capteur à la main, pas à pas", _MANUAL_PROCEDURE_TEXT),
    ("Convention des angles de montage (θx, θy, θz)", _CONVENTION_TEXT),
    ("Calibration automatique — expérimentale, à contrôler à la main", _AUTOMATIC_TEXT),
)


class SensorCalibrationPanel(QWidget):
    """Record the mounting angles of the mounted sensor and display the last
    ones recorded for this mounting and source geometry. The sensor itself
    (name, transduction gain) is declared and mounted in the 'Capteur' tab."""

    # theta_x, theta_y, theta_z
    save_calibration_requested = Signal(float, float, float)
    # theta_x, theta_y, theta_z — live trial, not recorded
    trial_rotation_requested = Signal(float, float, float)
    reset_to_default_requested = Signal()
    automatic_calibration_requested = Signal()

    def __init__(self, parent=None, orientation_view: Optional[QWidget] = None):
        """orientation_view: QWidget with show_mounting(matrix), shown right of
        the controls and fed with the active mounting matrix P."""
        super().__init__(parent)
        self._orientation_view = orientation_view

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        controls = QWidget()
        # Scrollable: an unfolded help section must never squeeze the text or push the buttons away.
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(controls)
        root.addWidget(scroll)
        if orientation_view is not None:
            root.addWidget(orientation_view, 1)

        layout = QVBoxLayout(controls)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        grp_procedure = QGroupBox("Aide")
        l_procedure = QVBoxLayout(grp_procedure)
        for title, text in _HELP_SECTIONS:
            lbl_procedure = QLabel(text)
            lbl_procedure.setTextFormat(Qt.RichText)
            lbl_procedure.setWordWrap(True)
            section = CollapsibleSection(title)
            section.set_content_widget(lbl_procedure)
            l_procedure.addWidget(section)
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
        self.btn_auto_calibration.setToolTip(
            "Pilote l'excitation (coupée, X, Y) au niveau réglé dans l'onglet Excitation, ajuste les angles "
            "sur les réponses du capteur et les applique en essai (non enregistrés)."
        )
        self.btn_auto_calibration.clicked.connect(self.automatic_calibration_requested.emit)
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

    def set_automatic_calibration_running(self, running: bool) -> None:
        """Lock the controls while the automatic calibration drives the excitation."""
        for widget in (self.btn_auto_calibration, self.btn_save, self.btn_reset_to_default,
                       self.spin_theta_x, self.spin_theta_y, self.spin_theta_z):
            widget.setEnabled(not running)

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
        if self._orientation_view is not None:
            self._orientation_view.show_mounting(dto.mounting_matrix)
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
