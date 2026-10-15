"""
Bar Transmission Calibration Panel

See bar_transmission_calibration_panel_intention.md.
"""

from PySide6.QtCore import Qt, QTimer, Signal, Slot
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
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

_MUTED = "color: #9AA0A6;"
_FG = "#DDDDDD"
_BG = "#1E1E1E"
_PROFILE_COLOR = "#4FC3F7"
_NO_RETURN_COLOR = "#E57373"
# Classification keys of the points read at rest -> (colour, legend label).
_REST_POINT_STYLE = {
    "on_bar": ("#81C784", "sur la barre"),
    "off_bar": ("#FFB74D", "hors barre"),
    "undecidable": ("#BA68C8", "indécidable"),
}
# The plot is redrawn at most this often (data arrive at ~10 Hz from the fly scan).
PLOT_REFRESH_MS = 150


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

        self.figure = Figure(facecolor=_BG, figsize=(6, 2.8))
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setMinimumHeight(260)
        self._plot_axis = ""
        self._profile = []  # (increment, distance_mm or None)
        self._threshold_mm = None
        self._coarse_fronts = ()
        self._rest_points = []  # (increment, mean_mm or None, std_mm or None, classification)
        self._brackets = {}  # front -> (bar side, floor side)
        self._plot_dirty = True
        self._plot_timer = QTimer(self)
        self._plot_timer.setInterval(PLOT_REFRESH_MS)
        self._plot_timer.timeout.connect(self.redraw_plot_if_needed)
        self._plot_timer.start()

        layout = QVBoxLayout(self)
        layout.addWidget(explanation)
        layout.addWidget(position_box)
        layout.addWidget(measure_box)
        layout.addWidget(self.lbl_status)
        layout.addWidget(self.canvas, stretch=2)
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

    # -- live plot ------------------------------------------------------------------

    @Slot(str)
    def reset_plot(self, axis: str) -> None:
        self._plot_axis = axis
        self._profile, self._rest_points, self._brackets = [], [], {}
        self._threshold_mm, self._coarse_fronts = None, ()
        self._plot_dirty = True

    @Slot(object)
    def add_profile_points(self, points) -> None:
        self._profile.extend(points)
        self._plot_dirty = True

    @Slot(object, float, float)
    def show_coarse_localization(self, threshold_mm, first_front: float, second_front: float) -> None:
        self._threshold_mm, self._coarse_fronts = threshold_mm, (first_front, second_front)
        self._plot_dirty = True

    @Slot(int, object, object, str)
    def add_rest_point(self, increment: int, mean_mm, std_mm, classification: str) -> None:
        self._rest_points.append((increment, mean_mm, std_mm, classification))
        self._plot_dirty = True

    @Slot(str, int, int)
    def show_front_bracket(self, front: str, on_bar_increment: int, off_bar_increment: int) -> None:
        self._brackets[front] = (on_bar_increment, off_bar_increment)
        self._plot_dirty = True

    @Slot()
    def redraw_plot_if_needed(self) -> None:
        """Called by the refresh timer: redraws only when data changed."""
        if not self._plot_dirty:
            return
        self._plot_dirty = False
        self._draw_plot()

    def _draw_plot(self) -> None:
        self.figure.clear()
        ax = self.figure.add_subplot(111, facecolor=_BG)
        bottom = ax.get_xaxis_transform()  # x in increments, y in axes fraction
        returns = [(n, d) for n, d in self._profile if d is not None]
        no_returns = [n for n, d in self._profile if d is None]
        if returns:
            ax.plot(*zip(*returns), ".", markersize=2, color=_PROFILE_COLOR, label="fly scan")
        if no_returns:
            ax.plot(no_returns, [0.02] * len(no_returns), "|", color=_NO_RETURN_COLOR, transform=bottom,
                    label="pas de retour")
        if self._threshold_mm is not None:
            ax.axhline(self._threshold_mm, color=_FG, linestyle="--", linewidth=1, label="seuil")
        for front in self._coarse_fronts:
            ax.axvline(front, color=_FG, linestyle=":", linewidth=1)
        for on_bar, off_bar in self._brackets.values():
            ax.axvspan(min(on_bar, off_bar), max(on_bar, off_bar), color=_FG, alpha=0.12)
        for key, (color, label) in _REST_POINT_STYLE.items():
            points = [p for p in self._rest_points if p[3] == key]
            measured = [p for p in points if p[1] is not None]
            if measured:
                ax.errorbar([p[0] for p in measured], [p[1] for p in measured],
                            yerr=[p[2] or 0.0 for p in measured], fmt="o", markersize=4, color=color,
                            capsize=2, label=label)
            empty = [p[0] for p in points if p[1] is None]
            if empty:
                ax.plot(empty, [0.06] * len(empty), "v", color=color, transform=bottom,
                        label=None if measured else label)
        ax.set_title(f"Axe {self._plot_axis}" if self._plot_axis else "Profil LIDAR", color=_FG, fontsize=8)
        ax.set_xlabel("position moteur (incréments)", color=_FG, fontsize=8)
        ax.set_ylabel("distance LIDAR (mm)", color=_FG, fontsize=8)
        ax.tick_params(colors=_FG, labelsize=7)
        ax.grid(True, linestyle=":", color="#333333")
        if ax.get_legend_handles_labels()[0]:
            ax.legend(fontsize=7, loc="upper right", facecolor=_BG, labelcolor=_FG)
        self.figure.tight_layout()
        self.canvas.draw_idle()
