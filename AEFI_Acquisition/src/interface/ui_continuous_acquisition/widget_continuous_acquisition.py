"""
Continuous Acquisition Widget - Infrastructure Layer

Responsibility:
- Combined widget for continuous acquisition (controls + visualizer)
- Single dockable component

Rationale:
- Controls and visualizer are tightly coupled
- Better UX when kept together
"""

from typing import Dict, List, Any
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QDoubleSpinBox,
    QGroupBox,
    QComboBox,
)
from PyQt6.QtCore import Qt
import pyqtgraph as pg  # type: ignore[import]

from .presenter_continuous_acquisition import ContinuousAcquisitionPresenter


class ContinuousAcquisitionWidget(QWidget):
    """
    Combined widget for continuous acquisition.
    
    Contains:
    - Controls (sample rate, duration, start/stop, status, display window)
    - Visualizer (time series graph for 6 channels)
    - Data is pushed from ContinuousAcquisitionPresenter via Qt signals
    """

    CHANNELS = [
        # X Axis
        dict(name="Ux In-Phase", label="ΔVx In-Phase", color="#4A90E2", style=Qt.PenStyle.SolidLine),
        dict(name="Ux Quadrature", label="ΔVx Quadrature", color="#4A90E2", style=Qt.PenStyle.DotLine),
        
        # Y Axis
        dict(name="Uy In-Phase", label="ΔVy In-Phase", color="#F4D03F", style=Qt.PenStyle.SolidLine),
        dict(name="Uy Quadrature", label="ΔVy Quadrature", color="#F4D03F", style=Qt.PenStyle.DotLine),
        
        # Z Axis
        dict(name="Uz In-Phase", label="ΔVz In-Phase", color="#E74C3C", style=Qt.PenStyle.SolidLine),
        dict(name="Uz Quadrature", label="ΔVz Quadrature", color="#E74C3C", style=Qt.PenStyle.DotLine),
    ]

    def __init__(self, presenter: ContinuousAcquisitionPresenter, parent=None) -> None:
        super().__init__(parent)
        self.presenter = presenter

        # Data buffers
        self.times: List[float] = []
        self.values: Dict[str, List[float]] = {ch["name"]: [] for ch in self.CHANNELS}
        self._t0: float | None = None

        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        layout.addWidget(self._build_controls_group())
        layout.addWidget(self._build_plot_group())

    def _build_controls_group(self) -> QWidget:
        group = QGroupBox("Continuous Acquisition Control")
        hl = QHBoxLayout(group)

        # Display rate (ex Sample Rate)
        hl.addWidget(QLabel("Display Rate (Hz):"))
        self.sample_rate_spin = QDoubleSpinBox()
        self.sample_rate_spin.setRange(1.0, 10_000.0)
        self.sample_rate_spin.setValue(20.0)
        # Connect dynamic update
        self.sample_rate_spin.valueChanged.connect(self._on_parameter_changed)
        hl.addWidget(self.sample_rate_spin)

        # Duration
        hl.addWidget(QLabel("Max duration (s):"))
        self.duration_spin = QDoubleSpinBox()
        self.duration_spin.setRange(0.0, 10.0)
        # 0.0 => pas de limite de durée (contrôle total via bouton Stop)
        self.duration_spin.setValue(0.0)
        # Connect dynamic update
        self.duration_spin.valueChanged.connect(self._on_parameter_changed)
        hl.addWidget(self.duration_spin)

        # Buttons start / stop
        self.btn_start = QPushButton("Start")
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setEnabled(False)
        hl.addWidget(self.btn_start)
        hl.addWidget(self.btn_stop)

        # Status
        self.lbl_status = QLabel("Idle")
        hl.addWidget(self.lbl_status)

        # Display window configuration (visualisation uniquement)
        # 0.0 => pas de limite, sinon fenêtre en secondes
        hl.addWidget(QLabel("Display window (s):"))
        self.window_length_spin = QDoubleSpinBox()
        self.window_length_spin.setRange(0.0, 60.0)
        self.window_length_spin.setValue(5.0)
        self.window_length_spin.valueChanged.connect(self._update_plot)
        hl.addWidget(self.window_length_spin)

        self.window_mode_combo = QComboBox()
        self.window_mode_combo.addItems(["Sliding window", "From start"])
        self.window_mode_combo.currentTextChanged.connect(self._update_plot)
        hl.addWidget(self.window_mode_combo)
        hl.addStretch()

        # Connect button actions
        self.btn_start.clicked.connect(self._on_start_clicked)
        self.btn_stop.clicked.connect(self._on_stop_clicked)

        return group

    def _build_plot_group(self) -> QWidget:
        group = QGroupBox("Continuous Signal (Time Series)")
        vlayout = QVBoxLayout(group)

        # Ligne de checkboxes pour choisir les signaux visibles
        controls_layout = QHBoxLayout()
        self.channel_checkboxes: Dict[str, Any] = {}
        for ch in self.CHANNELS:
            cb = QPushButton(ch["label"])
            # Utiliser un QPushButton checkable pour avoir un rendu plus compact
            cb.setCheckable(True)
            # Default check only In-Phase to avoid clutter
            cb.setChecked("In-Phase" in ch["name"]) 
            cb.setStyleSheet(f"QPushButton {{ color: {ch['color']}; font-weight: bold; }}"
                             f"QPushButton:checked {{ border: 2px solid {ch['color']}; }}")
            cb.setFixedWidth(160) # Ensure uniform size for alignment
            cb.clicked.connect(self._on_channel_toggled)
            self.channel_checkboxes[ch["name"]] = cb
            controls_layout.addWidget(cb)
        controls_layout.addStretch()
        vlayout.addLayout(controls_layout)

        # Plot pyqtgraph
        self.plot = pg.PlotWidget()
        self.plot.setBackground("#353535")
        self.plot.showGrid(x=True, y=True, alpha=0.2)
        self.plot.setLabel("left", "Voltage (V)")  # raw volts from measurement
        self.plot.setLabel("bottom", "Time (s)")
        self.plot.addLegend()

        self.curves: Dict[str, pg.PlotDataItem] = {}
        for ch in self.CHANNELS:
            pen = pg.mkPen(ch["color"], width=2, style=ch["style"])
            curve = self.plot.plot([], [], pen=pen, name=ch["label"])
            # Initialize visibility based on default checked state
            curve.setVisible("In-Phase" in ch["name"])
            self.curves[ch["name"]] = curve

        vlayout.addWidget(self.plot)
        return group

    def _connect_signals(self) -> None:
        self.presenter.acquisition_started.connect(self._on_acquisition_started)
        self.presenter.acquisition_stopped.connect(self._on_acquisition_stopped)
        self.presenter.sample_acquired.connect(self._on_sample_acquired)

    def _on_start_clicked(self) -> None:
        duration = self.duration_spin.value()
        max_duration = duration if duration > 0.0 else None
        params = {
            "sample_rate_hz": self.sample_rate_spin.value(),
            "max_duration_s": max_duration,
        }
        self.lbl_status.setText("Running...")
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.presenter.start_acquisition(params)

    def _on_stop_clicked(self) -> None:
        self.presenter.stop_acquisition()

    def _on_parameter_changed(self) -> None:
        """Called when user modifies rate/duration while running."""
        # Only update if running to avoid spamming stopped state (though service handles it gracefully)
        if self.btn_stop.isEnabled():
            duration = self.duration_spin.value()
            max_duration = duration if duration > 0.0 else None
            params = {
                "sample_rate_hz": self.sample_rate_spin.value(),
                "max_duration_s": max_duration,
            }
            self.presenter.update_parameters(params)

    def _on_acquisition_started(self, acquisition_id: str) -> None:
        self._reset_buffers()
        self.lbl_status.setText(f"Running (ID={acquisition_id[:8]})")

    def _on_acquisition_stopped(self, acquisition_id: str) -> None:
        self.lbl_status.setText(f"Stopped (ID={acquisition_id[:8]})")
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)

    def _on_sample_acquired(self, data: Dict[str, Any]) -> None:
        # Time base (relative)
        import datetime as _dt

        ts = _dt.datetime.fromisoformat(data["timestamp"]).timestamp()
        if self._t0 is None:
            self._t0 = ts
        t_rel = ts - self._t0
        self.times.append(t_rel)

        meas: Dict[str, float] = data.get("measurement", {})
        for ch in self.CHANNELS:
            name = ch["name"]
            val = float(meas.get(name, 0.0))
            self.values[name].append(val)

        self._update_plot()

    def _reset_buffers(self) -> None:
        self.times = []
        self.values = {ch["name"]: [] for ch in self.CHANNELS}
        self._t0 = None
        for curve in self.curves.values():
            curve.setData([], [])

    def _update_plot(self) -> None:
        if not self.times:
            return

        window = self.window_length_spin.value()
        mode_text = self.window_mode_combo.currentText() if self.window_mode_combo is not None else "Sliding window"

        t = self.times
        for name, curve in self.curves.items():
            ys_full = self.values.get(name, [])
            if not ys_full:
                curve.setData([], [])
                continue

            # Pas de fenêtre : tout l'historique
            # OU Mode "From start" : on veut tout voir depuis le début
            if window <= 0.0 or mode_text == "From start":
                curve.setData(t, ys_full)
                continue

            # Filtrage selon le mode "Sliding window"
            if mode_text.startswith("Sliding"):
                t_min = t[-1] - window
                # Garder uniquement les points récents
                idx_start = 0
                for i, ti in enumerate(t):
                    if ti >= t_min:
                        idx_start = i
                        break
                t_sub = t[idx_start:]
                y_sub = ys_full[idx_start:]
                curve.setData(t_sub, y_sub)

    def _on_channel_toggled(self) -> None:
        """
        Callback pour (dé)masquer des courbes en fonction des boutons checkables.
        """
        for name, btn in self.channel_checkboxes.items():
            visible = btn.isChecked()
            if name in self.curves:
                self.curves[name].setVisible(visible)
