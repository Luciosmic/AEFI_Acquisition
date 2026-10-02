"""
ADC Output Rate Characterization Widget

Section of the 'ADC' calibration tab: measures the ADC output data rate (ODR)
on the DRDY pin with the oscilloscope, at the current OSR or over a list of
OSR. Display only: every value comes computed in the DTOs (SI units,
converted to µs / MHz here).
"""

import re

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

_FG = "#DDDDDD"
_BG = "#1E1E1E"
_MUTED = "color: #888; font-style: italic;"
_ERROR = "color: #c62828;"
_COLUMNS = ("OSR", "ODR (Hz)", "Écart-type intervalles (µs)", "Intervalles réguliers / écartés", "f_MOD implicite (MHz)")
_EXPLANATION = (
    "Mesure la cadence de sortie de l'ADC sur la broche DRDY (une impulsion par conversion) à l'oscilloscope "
    "DSO-X 2014A : aucune hypothèse sur l'horloge. « Mesurer à l'OSR courant » ne change rien ; « Balayer les "
    "OSR » écrit chaque OSR de la liste dans le registre de l'ADC (sans l'enregistrer), puis remet l'OSR "
    "d'origine. Si l'ADC applique bien chaque OSR, la f_MOD implicite (ODR × OSR) est la même partout. "
    "Configuration ADC et flux d'acquisition sont verrouillés pendant la mesure ; un balayage est refusé "
    "pendant une lecture continue. La configuration de l'oscilloscope est restaurée après chaque capture."
)


def _parse_osr_values(text: str):
    return tuple(int(token) for token in re.split(r"[\s,;]+", text.strip()) if token)


class AdcOutputRateCharacterizationWidget(QGroupBox):
    # OSR values (tuple of int; empty = current OSR only), scope channel, probe ratio, periods per capture
    start_requested = Signal(object, int, float, int)

    def __init__(self, parent=None):
        super().__init__("Cadence de sortie de l'ADC (ODR) mesurée sur DRDY", parent)
        layout = QVBoxLayout(self)

        explanation = QLabel(_EXPLANATION)
        explanation.setWordWrap(True)
        explanation.setStyleSheet(_MUTED)
        layout.addWidget(explanation)

        form = QFormLayout()
        self.spin_channel = QSpinBox()
        self.spin_channel.setRange(1, 4)
        self.spin_channel.setValue(1)
        form.addRow("Voie de l'oscilloscope sur DRDY :", self.spin_channel)
        self.combo_probe = QComboBox()
        self.combo_probe.addItems(["10", "1"])
        form.addRow("Rapport de sonde (×) :", self.combo_probe)
        self.edit_osr_values = QLineEdit()
        self.edit_osr_values.setToolTip("OSR à balayer, séparés par des virgules ou des espaces (valeurs de l'ADS131A04).")
        form.addRow("OSR à balayer :", self.edit_osr_values)
        self.spin_periods = QSpinBox()
        self.spin_periods.setRange(3, 100000)
        self.spin_periods.setValue(50)
        self.spin_periods.setToolTip("Périodes de DRDY par capture (fixe la fenêtre de l'oscilloscope).")
        form.addRow("Périodes par capture :", self.spin_periods)
        layout.addLayout(form)

        buttons = QHBoxLayout()
        self.btn_current = QPushButton("Mesurer à l'OSR courant")
        self.btn_current.clicked.connect(lambda: self._emit_start(()))
        self.btn_sweep = QPushButton("Balayer les OSR")
        self.btn_sweep.clicked.connect(self._on_sweep_clicked)
        buttons.addWidget(self.btn_current)
        buttons.addWidget(self.btn_sweep)
        layout.addLayout(buttons)

        self.lbl_status = QLabel()
        self.lbl_status.setWordWrap(True)
        layout.addWidget(self.lbl_status)

        self.table = QTableWidget(0, len(_COLUMNS))
        self.table.setHorizontalHeaderLabels(_COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setMinimumHeight(160)
        layout.addWidget(self.table)

        self.figure = Figure(facecolor=_BG, figsize=(6, 2.4))
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setMinimumHeight(220)
        layout.addWidget(self.canvas)

        self.lbl_result = QLabel()
        self.lbl_result.setWordWrap(True)
        self.lbl_result.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.lbl_result)

        self._points = []
        self._draw(mean_modulator_frequency_hz=None)

    def _on_sweep_clicked(self) -> None:
        try:
            values = _parse_osr_values(self.edit_osr_values.text())
        except ValueError:
            self.set_status_message(f"Erreur: OSR illisibles « {self.edit_osr_values.text()} » — entiers séparés par des virgules")
            return
        if not values:
            self.set_status_message("Erreur: aucun OSR à balayer")
            return
        self._emit_start(values)

    def _emit_start(self, osr_values) -> None:
        self.start_requested.emit(osr_values, self.spin_channel.value(), float(self.combo_probe.currentText()),
                                  self.spin_periods.value())

    # -- presenter slots ----------------------------------------------------------

    def set_request_defaults(self, osr_values) -> None:
        self.edit_osr_values.setText(", ".join(str(v) for v in osr_values))

    def set_running(self, running: bool) -> None:
        for widget in (self.btn_current, self.btn_sweep, self.spin_channel, self.combo_probe, self.edit_osr_values,
                       self.spin_periods):
            widget.setEnabled(not running)
        if running:
            self._points = []
            self.table.setRowCount(0)
            self.lbl_result.clear()
            self._draw(mean_modulator_frequency_hz=None)

    def set_status_message(self, message: str) -> None:
        self.lbl_status.setStyleSheet(_ERROR if message.startswith("Erreur") else _MUTED)
        self.lbl_status.setText(message)

    def add_point(self, point) -> None:
        self._points.append(point)
        row = self.table.rowCount()
        self.table.insertRow(row)
        for column, text in enumerate((
            f"{point.oversampling_ratio}",
            f"{point.output_rate_hz:.4f}",
            f"{point.interval_std_s * 1e6:.3f}",
            f"{point.regular_interval_count} / {point.irregular_interval_count}",
            f"{point.implied_modulator_frequency_hz / 1e6:.6f}",
        )):
            self.table.setItem(row, column, QTableWidgetItem(text))
        self._draw(mean_modulator_frequency_hz=None)

    def show_result(self, result) -> None:
        self._points = list(result.points)
        self.lbl_result.setText(
            f"f_MOD moyenne {result.mean_modulator_frequency_hz / 1e6:.6f} MHz, écart relatif max entre OSR "
            f"{result.max_modulator_frequency_relative_deviation * 100:.4f} % — OSR remis à "
            f"{result.restored_oversampling_ratio} — {result.instrument}.\n"
            "f_MOD et la courbe ODR(OSR) sont pré-remplies dans la caractérisation ci-dessus : vérifier, "
            "nommer le composant, puis « Enregistrer la caractérisation »."
        )
        self._draw(mean_modulator_frequency_hz=result.mean_modulator_frequency_hz)

    # -- plot ---------------------------------------------------------------------

    def _draw(self, mean_modulator_frequency_hz) -> None:
        self.figure.clear()
        ax = self.figure.add_subplot(111, facecolor=_BG)
        osr = [p.oversampling_ratio for p in self._points]
        ax.plot(osr, [p.output_rate_hz for p in self._points], "o", color="#4FC3F7", label="ODR mesurée (DRDY)")
        if mean_modulator_frequency_hz and osr:
            line = sorted(osr)
            ax.plot(line, [mean_modulator_frequency_hz / o for o in line], "-", color="#81C784", linewidth=1,
                    label="f_MOD moyenne / OSR")
        if osr:  # log axes without data make matplotlib raise on draw
            ax.set_xscale("log", base=2)
            ax.set_yscale("log")
        ax.set_xlabel("OSR", color=_FG, fontsize=8)
        ax.set_ylabel("ODR (Hz)", color=_FG, fontsize=8)
        ax.tick_params(colors=_FG, labelsize=7)
        ax.grid(True, which="both", linestyle=":", color="#333333")
        if osr:
            ax.legend(fontsize=7)
        self.figure.tight_layout()
        self.canvas.draw_idle()
