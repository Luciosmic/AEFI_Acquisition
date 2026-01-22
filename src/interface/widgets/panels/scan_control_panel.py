from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QPushButton, QGroupBox, QFormLayout,
    QCheckBox
)
from PySide6.QtCore import Signal
import json
import os

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

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._connect_signals()
        self._load_config()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Style
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
            QLineEdit, QComboBox {
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
        
        # --- Scan Configuration Group ---
        config_group = QGroupBox("Scan Configuration")
        form_layout = QFormLayout()
        form_layout.setSpacing(8)
        form_layout.setContentsMargins(15, 20, 15, 15)
        
        self.input_x_min = QLineEdit("600.0")
        self.input_x_max = QLineEdit("800.0")
        self.input_x_nb = QLineEdit("81")
        
        self.input_y_min = QLineEdit("600.0")
        self.input_y_max = QLineEdit("800.0")
        self.input_y_nb = QLineEdit("81")
        
        self.input_stabilization = QLineEdit("300") # ms
        self.input_averaging = QLineEdit("10") # samples
        
        self.combo_pattern = QComboBox()
        self.combo_pattern.addItems(["RASTER", "SERPENTINE", "SPIRAL"])
        
        form_layout.addRow("X Min (mm):", self.input_x_min)
        form_layout.addRow("X Max (mm):", self.input_x_max)
        form_layout.addRow("X Points:", self.input_x_nb)
        form_layout.addRow("Y Min (mm):", self.input_y_min)
        form_layout.addRow("Y Max (mm):", self.input_y_max)
        form_layout.addRow("Y Points:", self.input_y_nb)
        form_layout.addRow("Stabilization (ms):", self.input_stabilization)
        form_layout.addRow("Averaging (samples):", self.input_averaging)
        form_layout.addRow("Pattern:", self.combo_pattern)
        
        config_group.setLayout(form_layout)
        layout.addWidget(config_group)

        # --- Export Configuration Group ---
        export_group = QGroupBox("Export Configuration")
        export_layout = QFormLayout()
        export_layout.setSpacing(8)
        export_layout.setContentsMargins(15, 20, 15, 15)

        self.checkbox_export_enabled = QCheckBox("Enable export")
        self.checkbox_export_enabled.setChecked(True)

        self.input_export_filename = QLineEdit("scan")
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
        
        control_group.setLayout(btn_layout)
        layout.addWidget(control_group)
        
        # --- Status ---
        self.lbl_status = QLabel("Status: Ready")
        self.lbl_status.setStyleSheet("color: #AAA; font-size: 12px; padding: 5px;")
        layout.addWidget(self.lbl_status)
        
        layout.addStretch()

    def _connect_signals(self):
        self.btn_start.clicked.connect(self._on_start_clicked)
        self.btn_stop.clicked.connect(self.scan_stop_requested)
        self.btn_pause.clicked.connect(self.scan_pause_requested)
        self.btn_resume.clicked.connect(self.scan_resume_requested)

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
            "export_enabled": self.checkbox_export_enabled.isChecked(),
            "export_output_directory": self.input_export_directory.text(),
            "export_filename_base": self.input_export_filename.text(),
            "export_format": self.combo_export_format.currentText(),
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
        """
        Load scan configuration from JSON file.
        Falls back to UI defaults if file doesn't exist or is invalid.
        """
        config_path = os.path.join(".aefi_acquisition", "configs", "scan_default_config.json")
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Load scan configuration
                scan_config = config.get("scan_config", {})
                if scan_config:
                    self.input_x_min.setText(str(scan_config.get("x_min", 600.0)))
                    self.input_x_max.setText(str(scan_config.get("x_max", 800.0)))
                    self.input_x_nb.setText(str(scan_config.get("x_nb_points", 81)))
                    self.input_y_min.setText(str(scan_config.get("y_min", 600.0)))
                    self.input_y_max.setText(str(scan_config.get("y_max", 800.0)))
                    self.input_y_nb.setText(str(scan_config.get("y_nb_points", 81)))
                    self.input_stabilization.setText(str(scan_config.get("stabilization_delay_ms", 300)))
                    self.input_averaging.setText(str(scan_config.get("averaging_per_position", 10)))
                    
                    # Set pattern in combo box
                    pattern = scan_config.get("scan_pattern", "SERPENTINE")
                    index = self.combo_pattern.findText(pattern)
                    if index >= 0:
                        self.combo_pattern.setCurrentIndex(index)
                
                # Load export configuration
                export_config = config.get("export_config", {})
                if export_config:
                    self.checkbox_export_enabled.setChecked(export_config.get("enabled", True))
                    self.input_export_filename.setText(export_config.get("filename_base", "scan"))
                    self.input_export_directory.setText(export_config.get("output_directory", ""))
                    
                    # Set format in combo box
                    format_str = export_config.get("format", "CSV")
                    format_index = self.combo_export_format.findText(format_str)
                    if format_index >= 0:
                        self.combo_export_format.setCurrentIndex(format_index)
                
                print(f"[ScanControlPanel] Configuration loaded from {config_path}")
            else:
                print(f"[ScanControlPanel] Config file not found at {config_path}, using UI defaults")
        except json.JSONDecodeError as e:
            print(f"[ScanControlPanel] Invalid JSON in config file: {e}, using UI defaults")
        except Exception as e:
            print(f"[ScanControlPanel] Error loading config: {e}, using UI defaults")