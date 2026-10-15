"""
Bar Transmission Calibration Panel

See bar_transmission_calibration_panel_intention.md.
"""

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

_MUTED = "color: #9AA0A6;"


class BarTransmissionCalibrationPanel(QWidget):
    """« Transmission (barre) » tab: live motor increments, L, axis, measure, record."""

    measure_requested = Signal(str, float)  # axis, bar length (mm)
    cancel_requested = Signal()
    record_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        explanation = QLabel(
            "Mesure de travel_per_motor_revolution_mm avec une barre de longueur connue vue par le LIDAR : "
            "homing, fly scan de butée à butée, puis encadrement des deux fronts à l'arrêt. "
            "La barre doit tenir entièrement dans la course, avec du sol de chaque côté. "
            "L'axe mesuré revient à l'origine à la fin."
        )
        explanation.setWordWrap(True)
        explanation.setStyleSheet(_MUTED)

        position_box = QGroupBox("Position moteur (incréments)")
        position_form = QFormLayout(position_box)
        self.lbl_x_increments = QLabel("—")
        self.lbl_y_increments = QLabel("—")
        self.lbl_moving = QLabel("")
        position_form.addRow("X :", self.lbl_x_increments)
        position_form.addRow("Y :", self.lbl_y_increments)
        position_form.addRow("", self.lbl_moving)

        measure_box = QGroupBox("Mesure")
        measure_form = QFormLayout(measure_box)
        self.spin_bar_length = QDoubleSpinBox()
        self.spin_bar_length.setRange(1.0, 1500.0)
        self.spin_bar_length.setDecimals(3)
        self.spin_bar_length.setSuffix(" mm")
        self.spin_bar_length.setValue(500.0)
        self.combo_axis = QComboBox()
        self.combo_axis.addItems(["X", "Y"])
        measure_form.addRow("Longueur L de la barre :", self.spin_bar_length)
        measure_form.addRow("Axe :", self.combo_axis)
        buttons = QHBoxLayout()
        self.btn_measure = QPushButton("Mesurer")
        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.setEnabled(False)
        self.btn_record = QPushButton("Enregistrer (moyenne X/Y)")
        buttons.addWidget(self.btn_measure)
        buttons.addWidget(self.btn_cancel)
        buttons.addStretch()
        buttons.addWidget(self.btn_record)
        measure_form.addRow(buttons)

        self.lbl_status = QLabel("")
        self.lbl_status.setWordWrap(True)
        self.txt_progress = QPlainTextEdit()
        self.txt_progress.setReadOnly(True)
        self.txt_progress.setMaximumBlockCount(500)

        results_box = QGroupBox("Résultats")
        results_layout = QVBoxLayout(results_box)
        self.lbl_result = {"X": QLabel("X : non mesuré"), "Y": QLabel("Y : non mesuré")}
        for label in self.lbl_result.values():
            label.setWordWrap(True)
            label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            results_layout.addWidget(label)
        self.lbl_mean = QLabel("")
        self.lbl_mean.setWordWrap(True)
        results_layout.addWidget(self.lbl_mean)

        layout = QVBoxLayout(self)
        layout.addWidget(explanation)
        layout.addWidget(position_box)
        layout.addWidget(measure_box)
        layout.addWidget(self.lbl_status)
        layout.addWidget(self.txt_progress, stretch=1)
        layout.addWidget(results_box)

        self.btn_measure.clicked.connect(
            lambda: self.measure_requested.emit(self.combo_axis.currentText(), self.spin_bar_length.value())
        )
        self.btn_cancel.clicked.connect(self.cancel_requested.emit)
        self.btn_record.clicked.connect(self.record_requested.emit)

    @Slot(int, int, bool)
    def on_increments_updated(self, x_increments: int, y_increments: int, is_moving: bool) -> None:
        self.lbl_x_increments.setText(str(x_increments))
        self.lbl_y_increments.setText(str(y_increments))
        self.lbl_moving.setText("en mouvement" if is_moving else "à l'arrêt")

    @Slot(bool)
    def set_running(self, running: bool) -> None:
        self.btn_measure.setEnabled(not running)
        self.btn_record.setEnabled(not running)
        self.btn_cancel.setEnabled(running)
        self.combo_axis.setEnabled(not running)
        self.spin_bar_length.setEnabled(not running)

    @Slot(str)
    def append_progress(self, message: str) -> None:
        self.txt_progress.appendPlainText(message)

    @Slot(str, str)
    def on_axis_result(self, axis: str, text: str) -> None:
        self.lbl_result[axis].setText(f"Axe {axis}\n{text}")

    @Slot(str)
    def on_mean(self, text: str) -> None:
        self.lbl_mean.setText(text)

    @Slot(str)
    def set_status_message(self, message: str) -> None:
        self.lbl_status.setText(message)
        self.txt_progress.appendPlainText(message)
