from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QPushButton, QGroupBox, QFormLayout,
    QCheckBox, QFileDialog, QGridLayout
)
from PySide6.QtCore import Signal
from pathlib import Path

from interface.logic.ui_config_store import UIConfigStore


class ScanControlPanel(QWidget):
    """
    Panel for configuring and controlling 2D scans.
    Migrated to Interface V2.
    """
    # Signals
    scan_start_requested = Signal(dict)  # parameters
    scan_stop_requested = Signal()
    scan_pause_requested = Signal()
    scan_resume_requested = Signal()

    def __init__(self, parent=None, config_store: UIConfigStore = None):
        super().__init__(parent)
        self._config_store = config_store or UIConfigStore()
        self._build_ui()
        self._connect_signals()
        self._load_config()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Same compact metrics as MotionPanelCompact / ExcitationPanel so the
        # three panels end up the same height when docked side by side.
        self.setStyleSheet("""
            QGroupBox {
                border: 1px solid #333;
                border-radius: 4px;
                margin-top: 6px;
                font-weight: bold;
                font-size: 11px;
                color: #CCC;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
            }
            QLabel { color: #DDD; font-size: 11px; }
            QLineEdit, QComboBox {
                background-color: #222;
                color: #FFF;
                border: 1px solid #444;
                padding: 2px;
                border-radius: 3px;
                font-size: 11px;
            }
            QCheckBox { color: #DDD; font-size: 11px; }
            QPushButton {
                background-color: #333;
                color: #EEE;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 3px 8px;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #444; }
            QPushButton:disabled {
                background-color: #222;
                color: #666;
            }
            QPushButton#btn_start {
                background-color: #2E7D32;
                border: 1px solid #43A047;
            }
            QPushButton#btn_start:hover { background-color: #388E3C; }
            QPushButton#btn_stop {
                background-color: #C62828;
                border: 1px solid #E53935;
            }
            QPushButton#btn_stop:hover { background-color: #D32F2F; }
        """)

        # --- Scan Configuration Group ---
        # 4-column grid (label, field, label, field): X/Y rows use cols 1-3 for
        # min/max/points, the other settings are paired two per row.
        config_group = QGroupBox("Scan Configuration")
        grid = QGridLayout(config_group)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(8)
        grid.setContentsMargins(10, 15, 10, 10)

        self.input_x_min = QLineEdit("600.0")
        self.input_x_max = QLineEdit("800.0")
        self.input_x_nb = QLineEdit("81")

        self.input_y_min = QLineEdit("600.0")
        self.input_y_max = QLineEdit("800.0")
        self.input_y_nb = QLineEdit("81")

        self.input_stabilization = QLineEdit("300") # ms
        self.input_averaging = QLineEdit("10") # samples

        self.combo_pattern = QComboBox()
        self.combo_pattern.addItems(["SERPENTINE", "RASTER"])

        self.combo_axis = QComboBox()
        self.combo_axis.addItems(["Y", "X"])  # Y = columns-first (preferred)

        self.checkbox_differential_mode = QCheckBox("Mesure différentielle (baseline sans excitation)")
        self.input_differential_settle_delay = QLineEdit("50")  # ms

        self.btn_save_scan_defaults = QPushButton("Set as default")

        for field in (
            self.input_x_min, self.input_x_max, self.input_x_nb,
            self.input_y_min, self.input_y_max, self.input_y_nb,
            self.input_stabilization, self.input_averaging,
            self.input_differential_settle_delay,
        ):
            field.setFixedWidth(70)

        for col, text in enumerate(("Min (mm)", "Max (mm)", "Points"), start=1):
            grid.addWidget(QLabel(text), 0, col)
        for row, (name, widgets) in enumerate((
            ("X:", (self.input_x_min, self.input_x_max, self.input_x_nb)),
            ("Y:", (self.input_y_min, self.input_y_max, self.input_y_nb)),
        ), start=1):
            grid.addWidget(QLabel(name), row, 0)
            for col, w in enumerate(widgets, start=1):
                grid.addWidget(w, row, col)

        grid.addWidget(QLabel("Stabilization (ms):"), 3, 0)
        grid.addWidget(self.input_stabilization, 3, 1)
        grid.addWidget(QLabel("Averaging:"), 3, 2)
        grid.addWidget(self.input_averaging, 3, 3)
        grid.addWidget(QLabel("Pattern:"), 4, 0)
        grid.addWidget(self.combo_pattern, 4, 1)
        grid.addWidget(QLabel("Axis (fast):"), 4, 2)
        grid.addWidget(self.combo_axis, 4, 3)
        grid.addWidget(self.checkbox_differential_mode, 5, 0, 1, 4)
        grid.addWidget(QLabel("Diff. settle (ms):"), 6, 0)
        grid.addWidget(self.input_differential_settle_delay, 6, 1)
        grid.addWidget(self.btn_save_scan_defaults, 6, 2, 1, 2)

        layout.addWidget(config_group)

        # --- Export Configuration Group ---
        export_group = QGroupBox("Export Configuration")
        export_grid = QGridLayout(export_group)
        export_grid.setHorizontalSpacing(6)
        export_grid.setVerticalSpacing(8)
        export_grid.setContentsMargins(10, 15, 10, 10)

        self.checkbox_export_enabled = QCheckBox("Enable export")
        self.checkbox_export_enabled.setChecked(True)

        self.input_export_filename = QLineEdit("scan")
        self.input_export_directory = QLineEdit("")
        self.input_export_directory.setPlaceholderText("~/Desktop/AEFI_Acquisition_Exports")

        self.input_export_filename.setFixedWidth(90)
        self.btn_browse_export_directory = QPushButton("Browse...")
        self.btn_save_export_defaults = QPushButton("Set as default")

        export_grid.addWidget(self.checkbox_export_enabled, 0, 0)
        export_grid.addWidget(QLabel("Filename base:"), 0, 1)
        export_grid.addWidget(self.input_export_filename, 0, 2)
        export_grid.addWidget(self.btn_save_export_defaults, 0, 3)
        export_grid.addWidget(QLabel("Output dir:"), 1, 0)
        export_grid.addWidget(self.input_export_directory, 1, 1, 1, 2)
        export_grid.addWidget(self.btn_browse_export_directory, 1, 3)

        layout.addWidget(export_group)

        # --- Control Group ---
        control_group = QGroupBox("Control")
        btn_layout = QHBoxLayout(control_group)
        btn_layout.setSpacing(6)
        btn_layout.setContentsMargins(10, 15, 10, 10)

        self.btn_start = QPushButton("START")
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

        layout.addWidget(control_group)

        # --- Status ---
        self.lbl_status = QLabel("Status: Ready")
        self.lbl_status.setStyleSheet("color: #AAA; font-size: 11px;")
        layout.addWidget(self.lbl_status)

        layout.addStretch()

    def _connect_signals(self):
        self.btn_start.clicked.connect(self._on_start_clicked)
        self.btn_stop.clicked.connect(self.scan_stop_requested)
        self.btn_pause.clicked.connect(self.scan_pause_requested)
        self.btn_resume.clicked.connect(self.scan_resume_requested)
        self.btn_browse_export_directory.clicked.connect(self._on_browse_export_directory)
        self.btn_save_export_defaults.clicked.connect(self._save_export_defaults)
        self.btn_save_scan_defaults.clicked.connect(self._save_scan_defaults)

    def _on_browse_export_directory(self):
        start_dir = self.input_export_directory.text() or str(Path.home() / "Desktop" / "AEFI_Acquisition_Exports")
        chosen = QFileDialog.getExistingDirectory(self, "Select export directory", start_dir)
        if chosen:
            self.input_export_directory.setText(chosen)

    def _on_start_clicked(self):
        """Gather parameters and emit signal."""
        params = {
            "x_min": self.input_x_min.text(),
            "x_max": self.input_x_max.text(),
            "x_nb_points": self.input_x_nb.text(),
            "y_min": self.input_y_min.text(),
            "y_max": self.input_y_max.text(),
            "y_nb_points": self.input_y_nb.text(),
            "stabilization_delay_ms": self.input_stabilization.text(),
            "averaging_per_position": self.input_averaging.text(),
            "scan_pattern": self.combo_pattern.currentText(),
            "scan_axis": self.combo_axis.currentText(),
            "differential_mode": self.checkbox_differential_mode.isChecked(),
            "differential_settle_delay_ms": self.input_differential_settle_delay.text(),
            "export_enabled": self.checkbox_export_enabled.isChecked(),
            "export_output_directory": self.input_export_directory.text(),
            "export_filename_base": self.input_export_filename.text(),
        }
        self.scan_start_requested.emit(params)

    def update_status(self, status: str):
        """Update status label."""
        self.lbl_status.setText(f"Status: {status}")

    def on_scan_started(self, scan_id: str):
        """Called when scan starts."""
        self.lbl_status.setText(f"Status: Running (ID: {scan_id})")
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_pause.setEnabled(True)
        self.btn_resume.setEnabled(False)

    def on_scan_completed(self, total_points: int):
        """Called when scan completes."""
        self.lbl_status.setText(f"Status: Completed ({total_points} points)")
        self._reset_buttons()

    def on_scan_failed(self, reason: str):
        """Called when scan fails."""
        self.lbl_status.setText(f"Status: Failed ({reason})")
        self._reset_buttons()

    def on_scan_cancelled(self, scan_id: str):
        """Called when scan is cancelled/stopped."""
        self.lbl_status.setText(f"Status: Cancelled")
        self._reset_buttons()

    def on_scan_paused(self, scan_id: str, current_point: int):
        """Called when scan is paused."""
        self.lbl_status.setText(f"Status: Paused (at point {current_point})")
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.btn_resume.setEnabled(True)

    def on_scan_resumed(self, scan_id: str, resume_point: int):
        """Called when scan is resumed."""
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
    
    def _load_config(self):
        """Populate the form from stored scan/export defaults, falling back to UI defaults."""
        scan_config = self._config_store.load_scan_config()
        if scan_config:
            self.input_x_min.setText(str(scan_config.get("x_min", 600.0)))
            self.input_x_max.setText(str(scan_config.get("x_max", 800.0)))
            self.input_x_nb.setText(str(scan_config.get("x_nb_points", 81)))
            self.input_y_min.setText(str(scan_config.get("y_min", 600.0)))
            self.input_y_max.setText(str(scan_config.get("y_max", 800.0)))
            self.input_y_nb.setText(str(scan_config.get("y_nb_points", 81)))
            self.input_stabilization.setText(str(scan_config.get("stabilization_delay_ms", 300)))
            self.input_averaging.setText(str(scan_config.get("averaging_per_position", 10)))
            self.checkbox_differential_mode.setChecked(scan_config.get("differential_mode", False))
            self.input_differential_settle_delay.setText(str(scan_config.get("differential_settle_delay_ms", 50)))

            pattern_index = self.combo_pattern.findText(scan_config.get("scan_pattern", "SERPENTINE"))
            if pattern_index >= 0:
                self.combo_pattern.setCurrentIndex(pattern_index)

            axis_index = self.combo_axis.findText(scan_config.get("scan_axis", "Y"))
            if axis_index >= 0:
                self.combo_axis.setCurrentIndex(axis_index)

        export_config = self._config_store.load_export_config()
        if export_config:
            self.checkbox_export_enabled.setChecked(export_config.get("enabled", True))
            self.input_export_filename.setText(export_config.get("filename_base", "scan"))
            self.input_export_directory.setText(export_config.get("output_directory", ""))

    def _save_scan_defaults(self):
        """Persist the current scan settings (including differential mode) as the new defaults."""
        scan_config = {
            "x_min": float(self.input_x_min.text()),
            "x_max": float(self.input_x_max.text()),
            "x_nb_points": int(self.input_x_nb.text()),
            "y_min": float(self.input_y_min.text()),
            "y_max": float(self.input_y_max.text()),
            "y_nb_points": int(self.input_y_nb.text()),
            "scan_pattern": self.combo_pattern.currentText(),
            "scan_axis": self.combo_axis.currentText(),
            "stabilization_delay_ms": int(self.input_stabilization.text()),
            "averaging_per_position": int(self.input_averaging.text()),
            "differential_mode": self.checkbox_differential_mode.isChecked(),
            "differential_settle_delay_ms": float(self.input_differential_settle_delay.text()),
        }
        try:
            self._config_store.save_scan_config(scan_config)
            self.lbl_status.setText("Status: Scan defaults saved")
        except (OSError, ValueError) as e:
            self.lbl_status.setText(f"Status: Failed to save scan defaults ({e})")

    def _save_export_defaults(self):
        """Persist the current export settings as the new defaults."""
        export_config = {
            "enabled": self.checkbox_export_enabled.isChecked(),
            "filename_base": self.input_export_filename.text(),
            "output_directory": self.input_export_directory.text(),
        }
        try:
            self._config_store.save_export_config(export_config)
            self.lbl_status.setText("Status: Export defaults saved")
        except OSError as e:
            self.lbl_status.setText(f"Status: Failed to save export defaults ({e})")