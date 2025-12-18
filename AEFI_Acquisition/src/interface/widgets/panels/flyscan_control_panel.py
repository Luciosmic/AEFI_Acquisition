"""
FlyScan Control Panel - UI Widget

Panel for configuring and controlling FlyScan operations.
FlyScan differs from StepScan:
- Continuous motion (no stops)
- Acquisition during motion
- Motion profile configuration
- Acquisition rate requirements
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QPushButton, QGroupBox, QFormLayout,
    QCheckBox, QDoubleSpinBox
)
from PySide6.QtCore import Signal

class FlyScanControlPanel(QWidget):
    """
    Panel for configuring and controlling FlyScan operations.
    """
    # Signals
    flyscan_start_requested = Signal(dict)  # parameters
    flyscan_stop_requested = Signal()
    flyscan_pause_requested = Signal()
    flyscan_resume_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Style (reuse from ScanControlPanel)
        self.setStyleSheet("""
            QGroupBox {
                border: 1px solid #333;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
                color: #CCC;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
            }
            QLabel { color: #DDD; }
            QLineEdit, QComboBox, QDoubleSpinBox {
                background-color: #222;
                color: #FFF;
                border: 1px solid #444;
                padding: 4px;
                border-radius: 3px;
            }
            QCheckBox {
                color: #DDD;
            }
            QPushButton {
                background-color: #333;
                color: #EEE;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #444;
            }
            QPushButton:disabled {
                background-color: #222;
                color: #666;
            }
            QPushButton#btn_start {
                background-color: #2E7D32;
                border: 1px solid #43A047;
            }
            QPushButton#btn_start:hover {
                background-color: #388E3C;
            }
            QPushButton#btn_stop {
                background-color: #C62828;
                border: 1px solid #E53935;
            }
            QPushButton#btn_stop:hover {
                background-color: #D32F2F;
            }
        """)
        
        # --- Scan Zone Configuration ---
        zone_group = QGroupBox("Scan Zone")
        form_layout = QFormLayout()
        form_layout.setSpacing(8)
        form_layout.setContentsMargins(15, 20, 15, 15)
        
        self.input_x_min = QLineEdit("0.0")
        self.input_x_max = QLineEdit("10.0")
        self.input_x_nb = QLineEdit("3")
        
        self.input_y_min = QLineEdit("0.0")
        self.input_y_max = QLineEdit("10.0")
        self.input_y_nb = QLineEdit("3")
        
        self.combo_pattern = QComboBox()
        self.combo_pattern.addItems(["RASTER", "SERPENTINE", "COMB"])
        
        form_layout.addRow("X Min (mm):", self.input_x_min)
        form_layout.addRow("X Max (mm):", self.input_x_max)
        form_layout.addRow("X Points:", self.input_x_nb)
        form_layout.addRow("Y Min (mm):", self.input_y_min)
        form_layout.addRow("Y Max (mm):", self.input_y_max)
        form_layout.addRow("Y Points:", self.input_y_nb)
        form_layout.addRow("Pattern:", self.combo_pattern)
        
        zone_group.setLayout(form_layout)
        layout.addWidget(zone_group)
        
        # --- Motion Profile Configuration ---
        motion_group = QGroupBox("Motion Profile")
        motion_layout = QFormLayout()
        motion_layout.setSpacing(8)
        motion_layout.setContentsMargins(15, 20, 15, 15)
        
        self.input_min_speed = QDoubleSpinBox()
        self.input_min_speed.setRange(0.01, 100.0)
        self.input_min_speed.setValue(0.1)
        self.input_min_speed.setSuffix(" mm/s")
        self.input_min_speed.setDecimals(2)
        
        self.input_target_speed = QDoubleSpinBox()
        self.input_target_speed.setRange(0.01, 100.0)
        self.input_target_speed.setValue(10.0)
        self.input_target_speed.setSuffix(" mm/s")
        self.input_target_speed.setDecimals(2)
        
        self.input_acceleration = QDoubleSpinBox()
        self.input_acceleration.setRange(0.01, 100.0)
        self.input_acceleration.setValue(5.0)
        self.input_acceleration.setSuffix(" mm/s²")
        self.input_acceleration.setDecimals(2)
        
        self.input_deceleration = QDoubleSpinBox()
        self.input_deceleration.setRange(0.01, 100.0)
        self.input_deceleration.setValue(5.0)
        self.input_deceleration.setSuffix(" mm/s²")
        self.input_deceleration.setDecimals(2)
        
        motion_layout.addRow("Min Speed:", self.input_min_speed)
        motion_layout.addRow("Target Speed:", self.input_target_speed)
        motion_layout.addRow("Acceleration:", self.input_acceleration)
        motion_layout.addRow("Deceleration:", self.input_deceleration)
        
        motion_group.setLayout(motion_layout)
        layout.addWidget(motion_group)
        
        # --- Acquisition Configuration ---
        acquisition_group = QGroupBox("Acquisition")
        acquisition_layout = QFormLayout()
        acquisition_layout.setSpacing(8)
        acquisition_layout.setContentsMargins(15, 20, 15, 15)
        
        self.input_desired_rate = QDoubleSpinBox()
        self.input_desired_rate.setRange(1.0, 1000.0)
        self.input_desired_rate.setValue(100.0)
        self.input_desired_rate.setSuffix(" Hz")
        self.input_desired_rate.setDecimals(1)
        
        self.input_max_spatial_gap = QDoubleSpinBox()
        self.input_max_spatial_gap.setRange(0.01, 10.0)
        self.input_max_spatial_gap.setValue(0.5)
        self.input_max_spatial_gap.setSuffix(" mm")
        self.input_max_spatial_gap.setDecimals(2)
        
        acquisition_layout.addRow("Desired Rate:", self.input_desired_rate)
        acquisition_layout.addRow("Max Spatial Gap:", self.input_max_spatial_gap)
        
        acquisition_group.setLayout(acquisition_layout)
        layout.addWidget(acquisition_group)
        
        # --- Export Configuration ---
        export_group = QGroupBox("Export Configuration")
        export_layout = QFormLayout()
        export_layout.setSpacing(8)
        export_layout.setContentsMargins(15, 20, 15, 15)

        self.checkbox_export_enabled = QCheckBox("Enable export")
        self.checkbox_export_enabled.setChecked(True)

        self.input_export_filename = QLineEdit("flyscan")
        self.input_export_directory = QLineEdit("")
        self.input_export_directory.setPlaceholderText("data_repository/")

        self.combo_export_format = QComboBox()
        self.combo_export_format.addItems(["CSV", "HDF5"])

        export_layout.addRow(self.checkbox_export_enabled)
        export_layout.addRow("Filename base:", self.input_export_filename)
        export_layout.addRow("Output directory:", self.input_export_directory)
        export_layout.addRow("Format:", self.combo_export_format)

        export_group.setLayout(export_layout)
        layout.addWidget(export_group)
        
        # --- Control Group ---
        control_group = QGroupBox("Control")
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.setContentsMargins(15, 15, 15, 15)
        
        self.btn_start = QPushButton("START FLYSCAN")
        self.btn_start.setObjectName("btn_start")
        self.btn_stop = QPushButton("STOP")
        self.btn_stop.setObjectName("btn_stop")
        self.btn_pause = QPushButton("Pause")
        self.btn_resume = QPushButton("Resume")
        
        self.btn_stop.setEnabled(False)
        self.btn_pause.setEnabled(False)
        self.btn_resume.setEnabled(False)
        
        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_pause)
        btn_layout.addWidget(self.btn_resume)
        btn_layout.addWidget(self.btn_stop)
        
        control_group.setLayout(btn_layout)
        layout.addWidget(control_group)
        
        # --- Status ---
        self.lbl_status = QLabel("Status: Ready")
        self.lbl_status.setStyleSheet("color: #AAA; font-size: 12px; padding: 5px;")
        layout.addWidget(self.lbl_status)
        
        layout.addStretch()

    def _connect_signals(self):
        self.btn_start.clicked.connect(self._on_start_clicked)
        self.btn_stop.clicked.connect(self.flyscan_stop_requested)
        self.btn_pause.clicked.connect(self.flyscan_pause_requested)
        self.btn_resume.clicked.connect(self.flyscan_resume_requested)

    def _on_start_clicked(self):
        """Gather parameters and emit signal."""
        params = {
            "x_min": self.input_x_min.text(),
            "x_max": self.input_x_max.text(),
            "x_nb_points": self.input_x_nb.text(),
            "y_min": self.input_y_min.text(),
            "y_max": self.input_y_max.text(),
            "y_nb_points": self.input_y_nb.text(),
            "scan_pattern": self.combo_pattern.currentText(),
            "motion_profile": {
                "min_speed": self.input_min_speed.value(),
                "target_speed": self.input_target_speed.value(),
                "acceleration": self.input_acceleration.value(),
                "deceleration": self.input_deceleration.value()
            },
            "desired_acquisition_rate_hz": self.input_desired_rate.value(),
            "max_spatial_gap_mm": self.input_max_spatial_gap.value(),
            "export_enabled": self.checkbox_export_enabled.isChecked(),
            "export_output_directory": self.input_export_directory.text(),
            "export_filename_base": self.input_export_filename.text(),
            "export_format": self.combo_export_format.currentText(),
        }
        self.flyscan_start_requested.emit(params)

    def update_status(self, status: str):
        """Update status label."""
        self.lbl_status.setText(f"Status: {status}")

    def on_flyscan_started(self, scan_id: str):
        """Called when FlyScan starts."""
        self.lbl_status.setText(f"Status: Running (ID: {scan_id})")
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_pause.setEnabled(True)
        self.btn_resume.setEnabled(False)

    def on_flyscan_completed(self, total_points: int):
        """Called when FlyScan completes."""
        self.lbl_status.setText(f"Status: Completed ({total_points} points)")
        self._reset_buttons()

    def on_flyscan_failed(self, reason: str):
        """Called when FlyScan fails."""
        self.lbl_status.setText(f"Status: Failed ({reason})")
        self._reset_buttons()

    def on_flyscan_cancelled(self, scan_id: str):
        """Called when FlyScan is cancelled/stopped."""
        self.lbl_status.setText(f"Status: Cancelled")
        self._reset_buttons()

    def on_flyscan_paused(self, scan_id: str, current_point: int):
        """Called when FlyScan is paused."""
        self.lbl_status.setText(f"Status: Paused (at point {current_point})")
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.btn_resume.setEnabled(True)

    def on_flyscan_resumed(self, scan_id: str, resume_point: int):
        """Called when FlyScan is resumed."""
        self.lbl_status.setText(f"Status: Running (resumed from point {resume_point})")
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_pause.setEnabled(True)
        self.btn_resume.setEnabled(False)

    def _reset_buttons(self):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_pause.setEnabled(False)
        self.btn_resume.setEnabled(False)

