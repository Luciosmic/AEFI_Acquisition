"""
Frequency Sweep Panel

See frequency_sweep_panel_intention.md. Display only: amplitudes and phases
come computed in the view models; the fields are handed to the presenter as-is.
"""

from typing import Optional

from PySide6.QtCore import QRegularExpression, Signal
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from interface.widgets.lift_off_input.lift_off_input import LIFT_OFF_LABEL, LiftOffInput
from interface.widgets.measured_object_selector.measured_object_selector import MeasuredObjectSelector
from interface.widgets.operator_selector.operator_selector import OperatorSelector

_FG = "#DDDDDD"
_BG = "#1E1E1E"
_MUTED = "color: #888; font-style: italic;"
_ERROR = "color: #c62828;"
_AXIS_COLORS = ("#4FC3F7", "#81C784", "#FFB74D")
_EXPLANATION = (
    "Balaye la fréquence d'excitation, avec le mode et les niveaux du panneau Excitation, et enregistre "
    "la réponse I/Q moyenne par axe à chaque fréquence. Rôle « Référence instrument » : table en position "
    "basse, sans objet. Rôle « Fond » : table à la hauteur de travail, sans objet. Rôle « Mesure objet » : "
    "même hauteur de table que le fond, objet posé. Excitation et flux "
    "d'acquisition sont verrouillés pendant le balayage ; la fréquence de l'opérateur est rétablie à la fin."
)
TABLE_HEIGHT_TOOLTIP = (
    "Hauteur de la table, en mm, lue sur le panneau de commande de la table.\n"
    "Un fond ne se réutilise qu'à hauteur égale : la saisie est obligatoire."
)


class FrequencySweepPanel(QWidget):
    start_requested = Signal(object)  # dict of the request fields
    stop_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        explanation = QLabel(_EXPLANATION)
        explanation.setWordWrap(True)
        explanation.setStyleSheet(_MUTED)
        layout.addWidget(explanation)

        form = QFormLayout()
        self.combo_role = QComboBox()
        self.combo_role.currentIndexChanged.connect(self._on_role_changed)
        form.addRow("Rôle :", self.combo_role)
        # Object measurement only: the object (registry, wired to MeasuredObjectPresenter) and its lift-off.
        self.measured_object_selector = MeasuredObjectSelector()
        form.addRow("Objet mesuré :", self.measured_object_selector)
        self.input_lift_off = LiftOffInput()
        form.addRow(LIFT_OFF_LABEL, self.input_lift_off)
        self.input_table_height = QLineEdit()
        self.input_table_height.setPlaceholderText("mm")
        self.input_table_height.setToolTip(TABLE_HEIGHT_TOOLTIP)
        self.input_table_height.setValidator(
            QRegularExpressionValidator(QRegularExpression(r"^-?\d{0,4}([.,]\d{0,3})?$"), self)
        )
        form.addRow("Hauteur de la table (mm) :", self.input_table_height)
        self.spin_start_hz = self._frequency_spin()
        form.addRow("Fréquence de début (Hz) :", self.spin_start_hz)
        self.spin_stop_hz = self._frequency_spin()
        form.addRow("Fréquence de fin (Hz) :", self.spin_stop_hz)
        self.spin_frequency_count = QSpinBox()
        self.spin_frequency_count.setRange(2, 1000)
        self.spin_frequency_count.setToolTip("Nombre de fréquences, en espacement logarithmique, bornes incluses.")
        form.addRow("Nombre de fréquences :", self.spin_frequency_count)
        self.spin_samples = QSpinBox()
        self.spin_samples.setRange(3, 100000)
        form.addRow("Échantillons par fréquence :", self.spin_samples)
        self.operator_selector = OperatorSelector()  # registry, wired to OperatorPresenter
        form.addRow("Opérateur :", self.operator_selector)
        layout.addLayout(form)

        buttons = QHBoxLayout()
        self.btn_start = QPushButton("Lancer le balayage")
        self.btn_start.clicked.connect(self._on_start_clicked)
        self.btn_stop = QPushButton("Arrêter")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_requested.emit)
        buttons.addWidget(self.btn_start)
        buttons.addWidget(self.btn_stop)
        layout.addLayout(buttons)

        self.lbl_status = QLabel()
        self.lbl_status.setWordWrap(True)
        layout.addWidget(self.lbl_status)

        self.figure = Figure(facecolor=_BG, figsize=(6, 4))
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setMinimumHeight(320)
        layout.addWidget(self.canvas, 1)

        self._points = []
        self._plot_pending = True
        self._running = False
        self._on_role_changed()

    @staticmethod
    def _frequency_spin() -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(0.001, 8_000_000.0)
        spin.setDecimals(3)
        return spin

    def _table_height_mm(self) -> Optional[float]:
        text = self.input_table_height.text().strip().replace(",", ".")
        if text in ("", ".", "-", "-."):
            return None
        return float(text)

    def _measures_an_object(self) -> bool:
        return self.combo_role.currentData() == "object_measurement"

    def _on_role_changed(self, *_args) -> None:
        enabled = self._measures_an_object() and not getattr(self, "_running", False)
        self.measured_object_selector.setEnabled(enabled)
        self.input_lift_off.setEnabled(enabled)

    def _on_start_clicked(self) -> None:
        operator = self.operator_selector.current_operator()
        measured_object = self.measured_object_selector.current_measured_object() if self._measures_an_object() else None
        self.start_requested.emit({
            "role": self.combo_role.currentData(),
            "start_hz": self.spin_start_hz.value(),
            "stop_hz": self.spin_stop_hz.value(),
            "frequency_count": self.spin_frequency_count.value(),
            "samples_per_frequency": self.spin_samples.value(),
            "table_height_mm": self._table_height_mm(),
            "operator_name": operator.name if operator else "",
            "operator_id": operator.operator_id if operator else "",
            "measured_object_name": measured_object.name if measured_object else "",
            "measured_object_id": measured_object.measured_object_id if measured_object else "",
            "lift_off_mm": self.input_lift_off.lift_off_mm() if self._measures_an_object() else None,
        })

    # -- presenter slots ----------------------------------------------------------

    def set_request_defaults(self, request, role_labels) -> None:
        self.combo_role.clear()
        for role, label in role_labels:
            self.combo_role.addItem(label, role)
        self.combo_role.setCurrentIndex(max(0, self.combo_role.findData(request.role)))
        self.spin_start_hz.setValue(request.start_hz)
        self.spin_stop_hz.setValue(request.stop_hz)
        self.spin_frequency_count.setValue(request.frequency_count)
        self.spin_samples.setValue(request.samples_per_frequency)

    def set_running(self, running: bool) -> None:
        for widget in (
            self.btn_start, self.combo_role, self.input_table_height, self.spin_start_hz, self.spin_stop_hz,
            self.spin_frequency_count, self.spin_samples, self.operator_selector,
        ):
            widget.setEnabled(not running)
        self.btn_stop.setEnabled(running)
        self._running = running
        self._on_role_changed()
        if running:
            self._points = []
            self._draw()

    def set_status_message(self, message: str) -> None:
        self.lbl_status.setStyleSheet(_ERROR if message.startswith("Erreur") else _MUTED)
        self.lbl_status.setText(message)

    def add_point(self, point) -> None:
        self._points.append(point)
        self._draw()

    # -- plot ---------------------------------------------------------------------

    def _draw(self) -> None:
        # matplotlib draws hidden canvases too: a panel not shown yet is plotted at its first show.
        self._plot_pending = True
        if self.isVisible():
            self._plot()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if self._plot_pending:
            self._plot()

    def _plot(self) -> None:
        self._plot_pending = False
        self.figure.clear()
        amplitude_ax = self.figure.add_subplot(211, facecolor=_BG)
        phase_ax = self.figure.add_subplot(212, facecolor=_BG, sharex=amplitude_ax)
        frequencies = [p.frequency_hz for p in self._points]
        for axis_index, (name, color) in enumerate(zip(("X", "Y", "Z"), _AXIS_COLORS)):
            amplitude_ax.plot(frequencies, [p.amplitude_v[axis_index] for p in self._points], "o-",
                              color=color, markersize=3, label=name)
            phase_ax.plot(frequencies, [p.phase_deg[axis_index] for p in self._points], "o-",
                          color=color, markersize=3, label=name)
        amplitude_ax.set_ylabel("amplitude (V)", color=_FG, fontsize=8)
        phase_ax.set_ylabel("phase (°)", color=_FG, fontsize=8)
        phase_ax.set_xlabel("fréquence (Hz)", color=_FG, fontsize=8)
        for ax in (amplitude_ax, phase_ax):
            ax.set_xscale("log")
            ax.tick_params(colors=_FG, labelsize=7)
            ax.grid(True, linestyle=":", color="#333333")
        if self._points:
            amplitude_ax.legend(fontsize=7, facecolor=_BG, labelcolor=_FG)
        self.figure.tight_layout()
        self.canvas.draw_idle()
