"""
Acquisition Throughput Characterization Widget

Section of the 'Microcontrôleur' calibration tab: sweeps the MCU averaging
n_avg (excitation cut) and shows, per n_avg, the sample period, rates and
noise, live, then the fitted T(n) = T0 + n/ODR and the recommended n_avg.
Display only: every value comes computed in the DTOs (SI units, converted
to ms / µV here).
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGroupBox,
    QHeaderView,
    QLabel,
    QPushButton,
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
_COLUMNS = (
    "n_avg",
    "Période (ms)",
    "Débit (éch./s)",
    "Conversions ADC/s",
    "σ (µV, 6 voies)",
    "Bruit en 1 s (µV)",
)
_EXPLANATION = (
    "Excitation coupée. Balaye n_avg = 1 → 127 (50 échantillons par point) au réglage ADC courant "
    "(OSR de l'onglet ADC, enregistré avec le résultat), puis restaure n_avg et l'excitation. "
    "« Bruit en 1 s » = σ·√période : le bruit atteignable en moyennant une seconde de mesure, "
    "le critère qui départage débit et moyennage. Dure environ une minute ; l'excitation est "
    "verrouillée pendant la mesure."
)


class AcquisitionThroughputCharacterizationWidget(QGroupBox):
    start_requested = Signal()

    def __init__(self, parent=None):
        super().__init__("Débit et bruit vs n_avg (mesure)", parent)
        layout = QVBoxLayout(self)

        explanation = QLabel(_EXPLANATION)
        explanation.setWordWrap(True)
        explanation.setStyleSheet(_MUTED)
        layout.addWidget(explanation)

        self.btn_start = QPushButton("Mesurer débit et bruit vs n_avg (excitation coupée)")
        self.btn_start.clicked.connect(self.start_requested.emit)
        layout.addWidget(self.btn_start)

        self.lbl_status = QLabel()
        self.lbl_status.setWordWrap(True)
        layout.addWidget(self.lbl_status)

        self.table = QTableWidget(0, len(_COLUMNS))
        self.table.setHorizontalHeaderLabels(_COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setMinimumHeight(180)
        layout.addWidget(self.table)

        self.figure = Figure(facecolor=_BG, figsize=(6, 2.6))
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setMinimumHeight(240)
        layout.addWidget(self.canvas)

        self.lbl_result = QLabel()
        self.lbl_result.setWordWrap(True)
        self.lbl_result.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.lbl_result)

        self._points = []
        self._draw(recommended_n_avg=None)

    # -- presenter slots ----------------------------------------------------------

    def set_running(self, running: bool) -> None:
        self.btn_start.setEnabled(not running)
        if running:
            self._points = []
            self.table.setRowCount(0)
            self.lbl_result.clear()
            self._draw(recommended_n_avg=None)

    def set_status_message(self, message: str) -> None:
        self.lbl_status.setStyleSheet(_ERROR if message.startswith("Erreur") else _MUTED)
        self.lbl_status.setText(message)

    def add_point(self, point) -> None:
        self._points.append(point)
        row = self.table.rowCount()
        self.table.insertRow(row)
        for column, text in enumerate((
            f"{point.n_avg}",
            f"{point.sample_period_s * 1e3:.2f}",
            f"{point.sample_rate_per_s:.1f}",
            f"{point.adc_conversions_per_s:.0f}",
            f"{point.noise_rms_v * 1e6:.3g}",
            f"{point.noise_in_one_second_v * 1e6:.3g}",
        )):
            self.table.setItem(row, column, QTableWidgetItem(text))
        self._draw(recommended_n_avg=None)

    def show_result(self, result) -> None:
        self._points = list(result.points)
        odr = f"{result.adc_output_rate_hz:.0f} Hz" if result.adc_output_rate_hz else "non résolue (le coût fixe domine)"
        self.lbl_result.setText(
            f"n_avg recommandé : {result.recommended_n_avg} (indicatif : bruit estimé à "
            f"±{result.noise_relative_uncertainty * 100:.0f} %, les n_avg plus proches que cela ne sont "
            f"pas départagés)  —  modèle T(n) = T₀ + n/ODR : "
            f"T₀ = {result.overhead_s * 1e3:.2f} ms, ODR = {odr}, écart max au modèle "
            f"{result.fit_max_relative_residual * 100:.1f} %  —  OSR {result.oversampling_ratio}, "
            f"excitation {result.excitation}.\n"
            "Les débits mesurés sont pré-remplis dans la caractérisation ci-dessus : "
            "vérifier, nommer le composant, puis « Enregistrer la caractérisation »."
        )
        self._draw(recommended_n_avg=result.recommended_n_avg)

    # -- plot ---------------------------------------------------------------------

    def _draw(self, recommended_n_avg) -> None:
        self.figure.clear()
        rate_ax = self.figure.add_subplot(121, facecolor=_BG)
        noise_ax = self.figure.add_subplot(122, facecolor=_BG)
        n = [p.n_avg for p in self._points]
        rate_ax.plot(n, [p.sample_rate_per_s for p in self._points], "o-", color="#4FC3F7")
        noise_ax.plot(n, [p.noise_in_one_second_v * 1e6 for p in self._points], "o-", color="#FFB74D")
        if recommended_n_avg is not None:
            for ax in (rate_ax, noise_ax):
                ax.axvline(recommended_n_avg, color="#81C784", linestyle="--", linewidth=1)
        for ax, ylabel in ((rate_ax, "débit (éch./s)"), (noise_ax, "bruit en 1 s (µV)")):
            ax.set_xscale("log", base=2)
            ax.set_xlabel("n_avg", color=_FG, fontsize=8)
            ax.set_ylabel(ylabel, color=_FG, fontsize=8)
            ax.tick_params(colors=_FG, labelsize=7)
            ax.grid(True, linestyle=":", color="#333333")
        self.figure.tight_layout()
        self.canvas.draw_idle()
