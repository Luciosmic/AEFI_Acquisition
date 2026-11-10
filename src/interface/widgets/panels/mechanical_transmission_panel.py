"""
Mechanical Transmission Panel

See mechanical_transmission_panel_intention.md.
"""

from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

_MUTED = "color: #888;"
_WARNING = "color: #d98c00; font-weight: bold;"


class MechanicalTransmissionPanel(QWidget):
    """Current transmission + form to record a new one (distance per increment, driver setting)."""

    # microsteps, driver_current_a, driver_peak_current_a, microns_per_pulse
    save_requested = Signal(int, float, float, float)

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)

        current_box = QGroupBox("Transmission en cours")
        current_layout = QVBoxLayout(current_box)
        self.lbl_headline = QLabel("—")
        self.lbl_headline.setWordWrap(True)
        self.lbl_headline.setStyleSheet("font-weight: bold;")
        self.lbl_detail = QLabel("")
        self.lbl_detail.setWordWrap(True)
        self.lbl_detail.setStyleSheet(_MUTED)
        self.lbl_warning = QLabel("")
        self.lbl_warning.setWordWrap(True)
        self.lbl_warning.setStyleSheet(_WARNING)
        self.lbl_warning.setVisible(False)
        for label in (self.lbl_headline, self.lbl_detail, self.lbl_warning):
            current_layout.addWidget(label)
        layout.addWidget(current_box)

        form_box = QGroupBox("Enregistrer une nouvelle transmission")
        form = QFormLayout(form_box)
        self.spin_microns = QDoubleSpinBox()
        self.spin_microns.setDecimals(3)
        self.spin_microns.setRange(0.001, 1000.0)
        self.spin_microns.setValue(20.0)
        self.spin_microns.setSuffix(" µm/incrément")
        self.spin_microns.setToolTip("Distance parcourue par impulsion moteur, mesurée sur le banc")
        self.spin_microsteps = QSpinBox()
        self.spin_microsteps.setRange(1, 256)
        self.spin_microsteps.setValue(16)
        self.spin_microsteps.setPrefix("1/")
        self.spin_microsteps.setToolTip("Micro-pas réglé sur le driver, auquel le µm/incrément a été mesuré")
        self.spin_current = QDoubleSpinBox()
        self.spin_current.setDecimals(2)
        self.spin_current.setRange(0.1, 20.0)
        self.spin_current.setValue(3.5)
        self.spin_current.setSuffix(" A")
        self.spin_peak = QDoubleSpinBox()
        self.spin_peak.setDecimals(2)
        self.spin_peak.setRange(0.1, 20.0)
        self.spin_peak.setValue(4.0)
        self.spin_peak.setSuffix(" A")
        form.addRow("Distance par incrément", self.spin_microns)
        form.addRow("Micro-pas du driver", self.spin_microsteps)
        form.addRow("Courant réglé", self.spin_current)
        form.addRow("Courant crête", self.spin_peak)
        self.btn_save = QPushButton("Enregistrer la transmission")
        form.addRow(self.btn_save)
        layout.addWidget(form_box)

        self.lbl_status = QLabel("")
        self.lbl_status.setWordWrap(True)
        layout.addWidget(self.lbl_status)
        layout.addStretch()

        self.btn_save.clicked.connect(self._on_save_clicked)

    def _on_save_clicked(self):
        self.save_requested.emit(
            self.spin_microsteps.value(), self.spin_current.value(), self.spin_peak.value(), self.spin_microns.value()
        )

    @Slot(object)
    def show_transmission(self, view_model) -> None:
        """Show the current transmission (or what is missing) and prefill the form with it."""
        self.lbl_headline.setText(view_model.headline)
        self.lbl_detail.setText(view_model.detail)
        self.lbl_warning.setText(view_model.warning)
        self.lbl_warning.setVisible(bool(view_model.warning))
        if view_model.is_recorded:
            self.spin_microns.setValue(view_model.microns_per_pulse)
            self.spin_microsteps.setValue(view_model.microsteps)
            self.spin_current.setValue(view_model.driver_current_a)
            self.spin_peak.setValue(view_model.driver_peak_current_a)

    @Slot(bool)
    def set_scan_running(self, running: bool) -> None:
        """A transmission recorded during a scan would mix two scales in its positions: not offered."""
        self.btn_save.setEnabled(not running)
        self.btn_save.setToolTip("Indisponible pendant un scan" if running else "")

    @Slot(str)
    def set_status_message(self, message: str) -> None:
        self.lbl_status.setText(message)
