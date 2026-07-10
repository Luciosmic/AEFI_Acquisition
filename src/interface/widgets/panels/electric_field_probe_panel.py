"""
Electric Field Probe Panel - Interface V2
Live monitoring panel for a generic electric_field_probe (today: Narda EP-601).
No phase/quadrature, no rotation — connection is manual (probe is auto-off
and times out often), never tied to app startup.
"""

from typing import Dict, List, Optional

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QDoubleSpinBox,
    QGroupBox,
    QFormLayout,
)
from PySide6.QtCore import Qt, Signal
import pyqtgraph as pg  # type: ignore[import]

AXIS_COLORS = ["#4A90E2", "#F4D03F", "#E74C3C", "#9B59B6", "#2ECC71", "#E67E22"]

_TOGGLE_STYLE = (
    "QPushButton { color: #888; border: 1px solid #555; border-radius: 3px; padding: 2px 6px; }"
    "QPushButton:checked { background-color: #27AE60; color: white; border: 1px solid #27AE60; font-weight: bold; }"
    "QPushButton:disabled { color: #444; border: 1px solid #333; }"
)


class ElectricFieldProbePanel(QWidget):
    """Live X/Y/Z (or mono/bi-axial) field reading panel, with on-demand connect and noise tare."""

    connect_requested = Signal()
    disconnect_requested = Signal()
    acquisition_start_requested = Signal(dict)
    acquisition_stop_requested = Signal()
    parameters_updated = Signal(dict)
    calibrate_noise_requested = Signal()
    reset_calibration_requested = Signal()
    noise_toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.curves: Dict[str, pg.PlotDataItem] = {}
        self.axis_labels: tuple = ()
        self.times: List[float] = []
        self.values: Dict[str, List[float]] = {}
        self._t0: Optional[float] = None

        vlayout = QVBoxLayout(self)
        vlayout.setContentsMargins(5, 5, 5, 5)
        vlayout.setSpacing(5)

        controls_layout = QHBoxLayout()

        # --- Connection group ---
        grp_conn = QGroupBox("Probe")
        l_conn = QVBoxLayout(grp_conn)
        self.btn_connect = QPushButton("Connect")
        self.btn_connect.clicked.connect(self._on_connect_clicked)
        self.lbl_probe_status = QLabel("● Not connected")
        self.lbl_probe_status.setStyleSheet("color: #888; font-weight: bold;")
        self.lbl_data_status = QLabel("● No data")
        self.lbl_data_status.setStyleSheet("color: #888;")
        l_conn.addWidget(self.btn_connect)
        l_conn.addWidget(self.lbl_probe_status)
        l_conn.addWidget(self.lbl_data_status)
        controls_layout.addWidget(grp_conn)

        # --- Acquisition group ---
        grp_params = QGroupBox("Acquisition")
        l_params = QFormLayout(grp_params)
        self.sample_rate_spin = QDoubleSpinBox()
        self.sample_rate_spin.setRange(0.1, 1000.0)
        self.sample_rate_spin.setValue(20.0)
        self.sample_rate_spin.setSuffix(" Hz")
        self.sample_rate_spin.valueChanged.connect(self._on_parameter_changed)
        l_params.addRow("Rate:", self.sample_rate_spin)
        controls_layout.addWidget(grp_params)

        grp_ctrl = QGroupBox("Control")
        l_ctrl = QVBoxLayout(grp_ctrl)
        self.btn_start = QPushButton("Start")
        self.btn_start.clicked.connect(self._on_start_clicked)
        self.btn_start.setStyleSheet(
            "background-color: #2ECC71; color: white; font-weight: bold;"
        )
        self.btn_start.setEnabled(False)
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.clicked.connect(self._on_stop_clicked)
        self.btn_stop.setStyleSheet(
            "background-color: #E74C3C; color: white; font-weight: bold;"
        )
        self.btn_stop.setEnabled(False)
        l_ctrl.addWidget(self.btn_start)
        l_ctrl.addWidget(self.btn_stop)
        controls_layout.addWidget(grp_ctrl)

        # --- Ambient noise tare ---
        grp_calib = QGroupBox("Ambient Noise")
        l_calib = QHBoxLayout(grp_calib)
        self.btn_calib_noise = QPushButton("Zero Noise")
        self.btn_calib_noise.setToolTip("Set current background as noise offset (tare)")
        self.btn_calib_noise.clicked.connect(self.calibrate_noise_requested.emit)
        self.btn_toggle_noise = QPushButton("ON")
        self.btn_toggle_noise.setCheckable(True)
        self.btn_toggle_noise.setEnabled(False)
        self.btn_toggle_noise.setFixedWidth(38)
        self.btn_toggle_noise.setStyleSheet(_TOGGLE_STYLE)
        self.btn_toggle_noise.toggled.connect(self.noise_toggled.emit)
        self.btn_reset_calib = QPushButton("Reset")
        self.btn_reset_calib.setStyleSheet("color: #E74C3C;")
        self.btn_reset_calib.clicked.connect(self.reset_calibration_requested.emit)
        self.lbl_noise_offset = QLabel("—")
        self.lbl_noise_offset.setStyleSheet(
            "color: #888; font-size: 10px; font-style: italic;"
        )
        l_calib.addWidget(self.btn_calib_noise)
        l_calib.addWidget(self.btn_toggle_noise)
        l_calib.addWidget(self.btn_reset_calib)
        l_calib.addWidget(self.lbl_noise_offset, stretch=1)
        controls_layout.addWidget(grp_calib)

        controls_layout.addStretch()
        vlayout.addLayout(controls_layout)

        self.plot = pg.PlotWidget()
        self.plot.setBackground("#353535")
        self.plot.showGrid(x=True, y=True, alpha=0.2)
        self.plot.setLabel("left", "Field (V/m)")
        self.plot.setLabel("bottom", "Time (s)")
        self.plot.addLegend()
        vlayout.addWidget(self.plot)

    # ------------------------------------------------------------------ #
    # Panel -> Presenter
    # ------------------------------------------------------------------ #

    def _on_connect_clicked(self):
        if self.btn_connect.text() == "Connect":
            self.connect_requested.emit()
        else:
            self.disconnect_requested.emit()

    def _on_start_clicked(self):
        params = {
            "sample_rate_hz": self.sample_rate_spin.value(),
            "max_duration_s": None,
        }
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.acquisition_start_requested.emit(params)

    def _on_stop_clicked(self):
        self.acquisition_stop_requested.emit()

    def _on_parameter_changed(self):
        if self.btn_stop.isEnabled():
            self.parameters_updated.emit(
                {
                    "sample_rate_hz": self.sample_rate_spin.value(),
                    "max_duration_s": None,
                }
            )

    # ------------------------------------------------------------------ #
    # Presenter -> Panel
    # ------------------------------------------------------------------ #

    def on_probe_connection_changed(self, connected: bool, label: str):
        if connected:
            self.btn_connect.setText("Disconnect")
            self.lbl_probe_status.setText(f"● {label}")
            self.lbl_probe_status.setStyleSheet("color: #2ECC71; font-weight: bold;")
            self.btn_start.setEnabled(True)
        else:
            self.btn_connect.setText("Connect")
            color = "#E74C3C" if label != "Disconnected" else "#888"
            self.lbl_probe_status.setText(f"● {label}")
            self.lbl_probe_status.setStyleSheet(f"color: {color}; font-weight: bold;")
            self.btn_start.setEnabled(False)
            self.btn_stop.setEnabled(False)
            self.lbl_data_status.setText("● No data")
            self.lbl_data_status.setStyleSheet("color: #888;")

    def on_probe_axes_defined(self, axis_labels: tuple):
        self.axis_labels = axis_labels
        self.plot.clear()
        self.plot.addLegend()
        self.curves = {}
        self._reset_buffers()
        for i, label in enumerate(axis_labels):
            color = AXIS_COLORS[i % len(AXIS_COLORS)]
            pen = pg.mkPen(color, width=2)
            self.curves[label] = self.plot.plot([], [], pen=pen, name=label)
        norm_pen = pg.mkPen("#FFFFFF", width=1, style=Qt.PenStyle.DotLine)
        self.curves["Norm"] = self.plot.plot([], [], pen=norm_pen, name="Norm")

    def on_acquisition_started(self, acquisition_id: str):
        self._reset_buffers()

    def on_acquisition_stopped(self, acquisition_id: str):
        self.btn_start.setEnabled(self.btn_connect.text() == "Disconnect")
        self.btn_stop.setEnabled(False)
        self.lbl_data_status.setText("● No data")
        self.lbl_data_status.setStyleSheet("color: #888;")

    def on_sample_acquired(self, data: dict):
        import datetime as _dt

        self.lbl_data_status.setText("● Receiving")
        self.lbl_data_status.setStyleSheet("color: #2ECC71; font-weight: bold;")

        ts = _dt.datetime.fromisoformat(data["timestamp"]).timestamp()
        if self._t0 is None:
            self._t0 = ts
        self.times.append(ts - self._t0)

        for key, curve in self.curves.items():
            self.values.setdefault(key, []).append(data.get(key, 0.0))
            curve.setData(self.times, self.values[key])

    def update_correction_states(self, enabled: bool, offset_str: str):
        self.btn_toggle_noise.blockSignals(True)
        self.btn_toggle_noise.setEnabled(True)
        self.btn_toggle_noise.setChecked(enabled)
        self.btn_toggle_noise.blockSignals(False)
        self.lbl_noise_offset.setText(offset_str)

    def _reset_buffers(self):
        self.times = []
        self.values = {key: [] for key in self.curves}
        self._t0 = None
        for curve in self.curves.values():
            curve.setData([], [])
