"""
Continuous Acquisition Panel - Interface V2
Combines controls and visualization in a single panel (passive view pattern).
"""

from typing import Dict, List, Any
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QDoubleSpinBox,
    QGroupBox,
    QComboBox,
    QFormLayout,
    QGridLayout,
)
from PySide6.QtCore import Qt, Signal
import pyqtgraph as pg  # type: ignore[import]


class ContinuousAcquisitionPanel(QWidget):
    """
    Single panel for continuous acquisition with controls and time series visualization.
    
    Features:
    - Control panel (sample rate, duration, display window)
    - Start/Stop buttons
    - Pyqtgraph time series plot for 6 channels
    - Channel visibility toggles
    """
    
    # Signals (passive view pattern)
    acquisition_start_requested = Signal(dict)  # parameters
    acquisition_stop_requested = Signal()
    parameters_updated = Signal(dict)  # live parameter changes

    CHANNELS = [
        # X Axis
        dict(name="Ux In-Phase", label="X In-Phase", color="#4A90E2", style=Qt.PenStyle.SolidLine),
        dict(name="Ux Quadrature", label="X Quadrature", color="#4A90E2", style=Qt.PenStyle.DotLine),
        
        # Y Axis
        dict(name="Uy In-Phase", label="Y In-Phase", color="#F4D03F", style=Qt.PenStyle.SolidLine),
        dict(name="Uy Quadrature", label="Y Quadrature", color="#F4D03F", style=Qt.PenStyle.DotLine),
        
        # Z Axis
        dict(name="Uz In-Phase", label="Z In-Phase", color="#E74C3C", style=Qt.PenStyle.SolidLine),
        dict(name="Uz Quadrature", label="Z Quadrature", color="#E74C3C", style=Qt.PenStyle.DotLine),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.channel_checkboxes = {}
        
        # Data buffers
        self.times: List[float] = []
        self.values: Dict[str, List[float]] = {ch["name"]: [] for ch in self.CHANNELS}
        self._t0: float | None = None
        
        # Main layout
        vlayout = QVBoxLayout(self)
        vlayout.setContentsMargins(5, 5, 5, 5)
        vlayout.setSpacing(5)

        # --- Controls Area ---
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0, 0, 0, 0)
        
        # 1. Acquisition Params
        grp_params = QGroupBox("Acquisition")
        l_params = QFormLayout(grp_params)
        l_params.setContentsMargins(5, 5, 5, 5)
        
        self.sample_rate_spin = QDoubleSpinBox()
        self.sample_rate_spin.setRange(0.1, 1000.0)
        self.sample_rate_spin.setValue(20.0)
        self.sample_rate_spin.setSuffix(" Hz")
        self.sample_rate_spin.valueChanged.connect(self._on_parameter_changed)
        l_params.addRow("Rate:", self.sample_rate_spin)

        # Remove fixed Duration control - use infinite by default
        # Add Window Display Control
        self.window_mode_combo = QComboBox()
        self.window_mode_combo.addItems(["From start", "Sliding window"])
        self.window_mode_combo.currentTextChanged.connect(self._on_window_mode_changed)
        l_params.addRow("Display:", self.window_mode_combo)

        self.lbl_time_slot = QLabel("Sliding duration (s)") # Stored so we can hide it
        self.window_length_spin = QDoubleSpinBox()
        self.window_length_spin.setRange(1.0, 600.0)
        self.window_length_spin.setValue(10.0)
        self.window_length_spin.setSuffix(" s")
        self.window_length_spin.valueChanged.connect(self._update_plot) # Only updates view
        l_params.addRow(self.lbl_time_slot, self.window_length_spin)

        controls_layout.addWidget(grp_params)

        # 2. Controls
        grp_ctrl = QGroupBox("Control")
        l_ctrl = QVBoxLayout(grp_ctrl)
        l_ctrl.setContentsMargins(5, 5, 5, 5)
        
        self.btn_start = QPushButton("Start")
        self.btn_start.clicked.connect(self._on_start_clicked)
        self.btn_start.setStyleSheet("background-color: #2ECC71; color: white; font-weight: bold;")
        
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.clicked.connect(self._on_stop_clicked)
        self.btn_stop.setStyleSheet("background-color: #E74C3C; color: white; font-weight: bold;")
        self.btn_stop.setEnabled(False)
        
        self.lbl_status = QLabel("Idle")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        l_ctrl.addWidget(self.btn_start)
        l_ctrl.addWidget(self.btn_stop)
        l_ctrl.addWidget(self.lbl_status)
        controls_layout.addWidget(grp_ctrl)
        
        # 3. Channel Toggles
        # Create a grid or flow for channels ? Let's just stack them horizontally or in a grid
        # To make it compact, maybe a 2-rows grid
        grp_channels = QGroupBox("Channels")
        # Layout inside group
        l_channels = QVBoxLayout(grp_channels)
        l_channels.setContentsMargins(2, 2, 2, 2)
        l_channels.setSpacing(2)

        # Create pairs (In-Phase / Quadrature)
        # Use Grid Layout: 3 Columns (X, Y, Z), 2 Rows (In-Phase, Quadrature)
        channel_grid_layout = QGridLayout() # Use a separate layout for buttons
        channel_grid_layout.setContentsMargins(2, 2, 2, 2)
        channel_grid_layout.setSpacing(5)
        
        for i, ch in enumerate(self.CHANNELS):
            cb = QPushButton(ch["label"])
            cb.setCheckable(True)
            # Default check only In-Phase to avoid clutter
            cb.setChecked("In-Phase" in ch["name"]) 
            cb.setStyleSheet(f"QPushButton {{ color: {ch['color']}; font-weight: bold; }}"
                             f"QPushButton:checked {{ border: 2px solid {ch['color']}; }}")
            cb.setFixedWidth(130)  # Compact width for labels (X In-Phase etc.)
            cb.clicked.connect(self._on_channel_toggled)
            self.channel_checkboxes[ch["name"]] = cb
            
            # Logic: Even index = In-Phase (Row 0), Odd index = Quadrature (Row 1)
            # Col = i // 2 (0, 1, 2)
            row = i % 2
            col = i // 2
            channel_grid_layout.addWidget(cb, row, col)
            
        l_channels.addLayout(channel_grid_layout) # Add grid layout to group
        controls_layout.addWidget(grp_channels) # Add group to main controls layout

        # 4. Calibration Controls
        grp_calib = QGroupBox("Signal Processing")
        l_calib = QVBoxLayout(grp_calib)
        l_calib.setContentsMargins(5, 5, 5, 5)
        
        self.btn_calib_noise = QPushButton("Zero Noise")
        self.btn_calib_noise.setToolTip("Set current background as noise offset (Zero)")
        self.btn_calib_noise.clicked.connect(self._on_calib_noise_clicked)
        
        self.btn_calib_phase = QPushButton("Align Phase")
        self.btn_calib_phase.setToolTip("Rotate Phase to maximize In-Phase component")
        self.btn_calib_phase.clicked.connect(self._on_calib_phase_clicked)
        
        self.btn_calib_primary = QPushButton("Null Primary")
        self.btn_calib_primary.setToolTip("Set current signal as Primary Field offset (Tare)")
        self.btn_calib_primary.clicked.connect(self._on_calib_primary_clicked)

        self.btn_reset_calib = QPushButton("Reset All")
        self.btn_reset_calib.setStyleSheet("color: red;")
        self.btn_reset_calib.clicked.connect(self._on_reset_calib_clicked)
        
        l_calib.addWidget(self.btn_calib_noise)
        l_calib.addWidget(self.btn_calib_phase)
        l_calib.addWidget(self.btn_calib_primary)
        l_calib.addWidget(self.btn_reset_calib)
        
        l_calib.addWidget(self.btn_reset_calib)
        
        controls_layout.addWidget(grp_calib)

        # 5. Coordinate Transform Controls
        grp_trans = QGroupBox("Coordinate Transform")
        l_trans = QVBoxLayout(grp_trans)
        l_trans.setContentsMargins(5, 5, 5, 5)
        
        self.btn_apply_rotation = QPushButton("Apply Rotation")
        self.btn_apply_rotation.setCheckable(True)
        self.btn_apply_rotation.setStyleSheet("""
            QPushButton:checked {
                background-color: #8E44AD; 
                color: white; 
                font-weight: bold;
            }
        """)
        self.btn_apply_rotation.toggled.connect(self._on_rotation_toggled)
        self.btn_apply_rotation.setToolTip("Transform Sensor Frame -> Source Frame using angles from 'Ref. Transform' panel.")
        
        self.lbl_angles_info = QLabel("Angles: [0, 0, 0]")
        self.lbl_angles_info.setStyleSheet("color: #AAA;")
        
        l_trans.addWidget(self.btn_apply_rotation)
        l_trans.addWidget(self.lbl_angles_info)
        
        controls_layout.addWidget(grp_trans)
        
        controls_layout.addStretch() # Add stretch to push groups to left
        vlayout.addLayout(controls_layout)

        # Plot pyqtgraph
        self.plot = pg.PlotWidget()
        self.plot.setBackground("#353535")
        self.plot.showGrid(x=True, y=True, alpha=0.2)
        self.plot.setLabel("left", "Voltage (V)")
        self.plot.setLabel("bottom", "Time (s)")
        self.plot.addLegend()

        self.curves: Dict[str, pg.PlotDataItem] = {}
        for ch in self.CHANNELS:
            pen = pg.mkPen(ch["color"], width=2, style=ch["style"])
            curve = self.plot.plot([], [], pen=pen, name=ch["label"])
            curve.setVisible("In-Phase" in ch["name"])
            self.curves[ch["name"]] = curve

        vlayout.addWidget(self.plot)


    def _on_start_clicked(self):
        """Gather parameters and emit signal."""
        params = {
            "sample_rate_hz": self.sample_rate_spin.value(),
            "max_duration_s": None,  # Infinite duration
        }
        self.lbl_status.setText("Running...")
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.acquisition_start_requested.emit(params)

    def _on_stop_clicked(self):
        """Request stop."""
        self.acquisition_stop_requested.emit()
        # UI state will be updated by presenter signal acquisition_stopped

    # Signals for Calibration
    calibrate_noise_requested = Signal()
    calibrate_phase_requested = Signal()
    calibrate_primary_requested = Signal()
    reset_calibration_requested = Signal()

    def _on_calib_noise_clicked(self):
        self.calibrate_noise_requested.emit()

    def _on_calib_phase_clicked(self):
        self.calibrate_phase_requested.emit()

    def _on_calib_primary_clicked(self):
        self.calibrate_primary_requested.emit()
        
    
    def _on_reset_calib_clicked(self):
        self.reset_calibration_requested.emit()

    # Signals for Rotation
    apply_rotation_toggled = Signal(bool)

    def _on_rotation_toggled(self, checked: bool):
        self.apply_rotation_toggled.emit(checked)
        
    def update_angles_display(self, angles: tuple):
        """Update the read-only angles label."""
        self.lbl_angles_info.setText(f"Angles: [{angles[0]:.1f}, {angles[1]:.1f}, {angles[2]:.1f}]")


    def _on_parameter_changed(self):
        """Called when user modifies rate while running."""
        if self.btn_stop.isEnabled():
            params = {
                "sample_rate_hz": self.sample_rate_spin.value(),
                "max_duration_s": None,  # Infinite duration
            }
            self.parameters_updated.emit(params)

    def on_acquisition_started(self, acquisition_id: str):
        """Called when acquisition starts (from presenter)."""
        self._reset_buffers()
        self.lbl_status.setText(f"Running (ID={acquisition_id[:8]})")

    def on_acquisition_stopped(self, acquisition_id: str):
        """Called when acquisition stops (from presenter)."""
        self.lbl_status.setText(f"Stopped (ID={acquisition_id[:8]})")
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)

    def on_sample_acquired(self, data: Dict[str, Any]):
        """Called for each new sample (from presenter)."""
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

    def _reset_buffers(self):
        """Clear data buffers."""
        self.times = []
        self.values = {ch["name"]: [] for ch in self.CHANNELS}
        self._t0 = None
        for curve in self.curves.values():
            curve.setData([], [])

    def _update_plot(self):
        """Refresh the plot based on display window settings."""
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

            # No window or "From start" mode: show all
            if window <= 0.0 or mode_text == "From start":
                curve.setData(t, ys_full)
                continue

            # Sliding window mode
            if mode_text.startswith("Sliding"):
                t_min = t[-1] - window
                idx_start = 0
                for i, ti in enumerate(t):
                    if ti >= t_min:
                        idx_start = i
                        break
                t_sub = t[idx_start:]
                y_sub = ys_full[idx_start:]
                curve.setData(t_sub, y_sub)

    def _on_channel_toggled(self):
        """Show/hide curves based on button states."""
        for name, btn in self.channel_checkboxes.items():
            visible = btn.isChecked()
            if name in self.curves:
                self.curves[name].setVisible(visible)
    
    def _on_window_mode_changed(self, mode_text: str):
        """Handle window mode changes and update plot."""
        self._update_time_slot_visibility(mode_text)
        self._update_plot()
    
    def _update_time_slot_visibility(self, mode_text: str):
        """Show/hide Time Slot controls based on window mode."""
        is_sliding = mode_text.startswith("Sliding")
        self.time_slot_label.setVisible(is_sliding)
        self.window_length_spin.setVisible(is_sliding)
