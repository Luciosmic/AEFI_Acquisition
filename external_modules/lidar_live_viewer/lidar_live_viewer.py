"""
Visualiseur LIDAR en direct, hors application AEFI.

Outil de banc : lit un LIDAR série ESP32 (lignes "<brut> <moyenne10>") via
l'adapter de l'application (Esp32SerialLidarAdapter, une seule règle de parsing)
et affiche la dernière distance, les statistiques glissantes et une courbe défilante.

    uv run python external_modules/lidar_live_viewer/lidar_live_viewer.py --port COM9
"""

import argparse
import logging
import signal
import statistics
import sys
import time
from collections import deque
from pathlib import Path

# Rendre `src/` importable, comme src/main.py (racine du dépôt = deux niveaux au-dessus).
SRC_DIR = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(SRC_DIR))

from PySide6.QtCore import Qt, QTimer  # noqa: E402  (PySide6 importé avant pyqtgraph : il choisit ce binding)
from PySide6.QtGui import QFont  # noqa: E402
from PySide6.QtWidgets import (  # noqa: E402
    QApplication, QGridLayout, QHBoxLayout, QLabel, QPushButton, QSpinBox, QVBoxLayout, QWidget,
)
import pyqtgraph as pg  # noqa: E402

from application.detection_devices.lidar_distance.ports.lidar_stream_error import (  # noqa: E402
    LidarUnavailableError,
)
from infrastructure.hardware.esp32_serial_lidar.adapter_lidar_distance_port import (  # noqa: E402
    Esp32SerialLidarAdapter,
)

logger = logging.getLogger(__name__)

POLL_PERIOD_MS = 50          # vidage de la file de l'adapter, sans bloquer l'UI
HISTORY_S = 60.0             # fenêtre de la courbe défilante
RATE_WINDOW_S = 5.0          # fenêtre de calcul du débit
DEFAULT_STATS_WINDOW = 25    # N lectures valides pour moyenne / écart-type


class LidarLiveViewer(QWidget):
    def __init__(self, adapter: Esp32SerialLidarAdapter, port: str, baudrate: int) -> None:
        super().__init__()
        self._adapter = adapter
        self._port = port
        self.setWindowTitle(f"LIDAR en direct — {port} @ {baudrate} Bd")
        self.resize(900, 600)

        self._history: deque = deque()        # (t, mm) des lectures valides, HISTORY_S dernières secondes
        self._arrivals: deque = deque()       # instants d'arrivée, pour le débit
        self._t0 = time.perf_counter()        # même horloge que l'adapter

        self._status = QLabel()
        self._status.setWordWrap(True)
        self._last_value = QLabel("—")
        big = QFont()
        big.setPointSize(48)
        big.setBold(True)
        self._last_value.setFont(big)
        self._last_value.setAlignment(Qt.AlignCenter)
        unit_note = QLabel("mm (unité supposée : brut × 1, non vérifiée)")
        unit_note.setAlignment(Qt.AlignCenter)

        self._window_spin = QSpinBox()
        self._window_spin.setRange(2, 10000)
        self._window_spin.setValue(DEFAULT_STATS_WINDOW)
        self._window_spin.valueChanged.connect(self._on_window_changed)
        self._reset_stats()
        reset_button = QPushButton("Remise à zéro des stats")
        reset_button.clicked.connect(self._on_reset)

        self._mean = QLabel("—")
        self._std = QLabel("—")
        self._count = QLabel("0")
        self._rate = QLabel("—")
        self._no_return = QLabel("0")
        stats = QGridLayout()
        rows = [
            ("N lectures valides (stats) :", self._window_spin),
            ("Moyenne (mm) :", self._mean),
            ("Écart-type (mm) :", self._std),
            ("Lectures reçues :", self._count),
            ("Débit (Hz) :", self._rate),
            ("« Pas de retour » :", self._no_return),
        ]
        for row, (label, widget) in enumerate(rows):
            stats.addWidget(QLabel(label), row, 0)
            stats.addWidget(widget, row, 1)
        stats.addWidget(reset_button, len(rows), 0, 1, 2)

        self._plot = pg.PlotWidget()
        self._plot.setLabel("left", "distance brute (mm, supposé)")
        self._plot.setLabel("bottom", "temps (s)")
        self._plot.showGrid(x=True, y=True, alpha=0.3)
        self._curve = self._plot.plot([], [], pen=pg.mkPen(width=2), symbol="o", symbolSize=4)

        top = QHBoxLayout()
        value_box = QVBoxLayout()
        value_box.addWidget(self._last_value)
        value_box.addWidget(unit_note)
        top.addLayout(value_box, 2)
        top.addLayout(stats, 1)
        layout = QVBoxLayout(self)
        layout.addWidget(self._status)
        layout.addLayout(top)
        layout.addWidget(self._plot, 1)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll)
        self._open()

    # --- cycle de vie du port ---

    def _open(self) -> None:
        try:
            self._adapter.open()
        except LidarUnavailableError as error:
            self._show_error(f"Port non ouvert : {error}\n"
                             f"Vérifier le câble, le numéro de port, et qu'aucun autre programme "
                             f"(application AEFI, moniteur série…) ne tient déjà {self._port}.")
            return
        self._status.setText(f"Connecté à {self._port} — en attente des lectures…")
        self._timer.start(POLL_PERIOD_MS)

    def _show_error(self, message: str) -> None:
        logger.error("LidarLiveViewer: %s", message)
        self._status.setText(message)
        self._status.setStyleSheet("color: #b00020; font-weight: bold;")

    def closeEvent(self, event) -> None:  # noqa: N802 (Qt)
        self._timer.stop()
        self._adapter.close()  # COM exclusif : libérer le port pour le prochain process
        logger.info("LidarLiveViewer: closed port=%s readings=%d no_return=%d",
                    self._port, self._n_readings, self._n_no_return)
        super().closeEvent(event)

    # --- lecture ---

    def _poll(self) -> None:
        got_any = False
        try:
            while (reading := self._adapter.read_distance(0)) is not None:
                self._ingest(reading)
                got_any = True
        except LidarUnavailableError as error:
            self._timer.stop()
            self._adapter.close()
            self._show_error(f"Flux LIDAR interrompu : {error}")
            return
        if got_any:
            self._refresh()

    def _ingest(self, reading) -> None:
        t = reading.timestamp_s - self._t0
        self._arrivals.append(t)
        self._n_readings += 1
        if not reading.distance.has_return:
            self._n_no_return += 1
            self._last_value.setText("pas de retour")
            return
        mm = reading.distance.distance_mm
        self._last_value.setText(f"{mm:.0f}")
        self._history.append((t, mm))
        self._window.append(mm)

    def _refresh(self) -> None:
        now = self._arrivals[-1]
        while self._history and self._history[0][0] < now - HISTORY_S:
            self._history.popleft()
        while self._arrivals and self._arrivals[0] < now - RATE_WINDOW_S:
            self._arrivals.popleft()
        if len(self._arrivals) >= 2 and self._arrivals[-1] > self._arrivals[0]:
            self._rate.setText(f"{(len(self._arrivals) - 1) / (self._arrivals[-1] - self._arrivals[0]):.1f}")
        if self._window:
            self._mean.setText(f"{statistics.fmean(self._window):.1f}  (sur {len(self._window)})")
            self._std.setText(f"{statistics.stdev(self._window):.1f}" if len(self._window) >= 2 else "—")
        self._count.setText(str(self._n_readings))
        self._no_return.setText(str(self._n_no_return))
        self._status.setText(f"Connecté à {self._port}")
        if self._history:
            ts, mms = zip(*self._history)
            self._curve.setData(ts, mms)
            self._plot.setXRange(max(0.0, now - HISTORY_S), max(now, HISTORY_S * 0.05), padding=0)

    # --- stats ---

    def _reset_stats(self) -> None:
        self._window: deque = deque(maxlen=self._window_spin.value())
        self._n_readings = 0
        self._n_no_return = 0

    def _on_reset(self) -> None:
        self._reset_stats()
        for label in (self._mean, self._std):
            label.setText("—")
        self._count.setText("0")
        self._no_return.setText("0")
        logger.info("LidarLiveViewer: stats reset port=%s", self._port)

    def _on_window_changed(self, n: int) -> None:
        self._window = deque(self._window, maxlen=n)


def main() -> int:
    parser = argparse.ArgumentParser(description="Visualiseur LIDAR série ESP32 en direct")
    parser.add_argument("--port", default="COM9")
    parser.add_argument("--baudrate", type=int, default=115200)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    app = QApplication(sys.argv)
    viewer = LidarLiveViewer(Esp32SerialLidarAdapter(args.port, args.baudrate), args.port, args.baudrate)
    viewer.show()
    # Ctrl+C dans le terminal ferme la fenêtre proprement (donc libère le port).
    signal.signal(signal.SIGINT, lambda *_: viewer.close())
    keepalive = QTimer()
    keepalive.timeout.connect(lambda: None)  # rend la main à Python pour traiter SIGINT
    keepalive.start(200)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
