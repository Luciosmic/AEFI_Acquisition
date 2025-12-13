from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QPushButton, QGroupBox, QFormLayout,
    QCheckBox,
)
from PyQt6.QtCore import Qt
from interface.ui_2d_scan.presenter_2d_scan import ScanPresenter

class ScanControlWidget(QWidget):
    """
    Widget for configuring and controlling the scan.
    Connects to ScanPresenter.
    """
    def __init__(self, presenter: ScanPresenter, parent=None):
        super().__init__(parent)
        self.presenter = presenter
        self.init_ui()
        self.connect_signals()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(6, 6, 6, 6)  # Reduced margins
        layout.setSpacing(4)  # Reduced spacing
        
        # --- Configuration Group ---
        config_group = QGroupBox("Scan Configuration")
        form_layout = QFormLayout()
        form_layout.setSpacing(4)  # Reduced spacing between rows
        form_layout.setContentsMargins(8, 8, 8, 8)  # Reduced margins
        
        self.input_x_min = QLineEdit("0.0")
        self.input_x_max = QLineEdit("10.0")
        self.input_x_nb = QLineEdit("10")
        
        self.input_y_min = QLineEdit("0.0")
        self.input_y_max = QLineEdit("10.0")
        self.input_y_nb = QLineEdit("10")
        
        
        self.input_speed = QLineEdit("46.0") # Default mm/s
        
        self.combo_pattern = QComboBox()
        self.combo_pattern.addItems(["RASTER", "SERPENTINE", "SPIRAL"])
        
        form_layout.addRow("X Min (mm):", self.input_x_min)
        form_layout.addRow("X Max (mm):", self.input_x_max)
        form_layout.addRow("X Points:", self.input_x_nb)
        form_layout.addRow("Y Min (mm):", self.input_y_min)
        form_layout.addRow("Y Max (mm):", self.input_y_max)
        form_layout.addRow("Y Points:", self.input_y_nb)
        form_layout.addRow("Speed (mm/s):", self.input_speed)
        form_layout.addRow("Pattern:", self.combo_pattern)
        
        config_group.setLayout(form_layout)
        layout.addWidget(config_group)

        # --- Export Group ---
        export_group = QGroupBox("Export Configuration")
        export_layout = QFormLayout()
        export_layout.setSpacing(4)
        export_layout.setContentsMargins(8, 8, 8, 8)

        self.checkbox_export_enabled = QCheckBox("Enable export")
        self.checkbox_export_enabled.setChecked(True)

        self.input_export_filename = QLineEdit("scan")
        self.input_export_directory = QLineEdit("")
        self.input_export_directory.setPlaceholderText("data_repository/")

        self.combo_export_format = QComboBox()
        # Default to HDF5 (recommended for scans), CSV kept as alternative.
        self.combo_export_format.addItems(["HDF5", "CSV"])

        export_layout.addRow(self.checkbox_export_enabled)
        export_layout.addRow("Filename base:", self.input_export_filename)
        export_layout.addRow("Output directory:", self.input_export_directory)
        export_layout.addRow("Format:", self.combo_export_format)

        export_group.setLayout(export_layout)
        layout.addWidget(export_group)
        
        # --- Control Group ---
        control_group = QGroupBox("Control")
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(4)
        btn_layout.setContentsMargins(8, 8, 8, 8)
        
        self.btn_start = QPushButton("Start")
        self.btn_stop = QPushButton("Stop")
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
        layout.addWidget(self.lbl_status)
        
        # Remove stretch to avoid wasted space
        self.setLayout(layout)
        
    def connect_signals(self):
        # UI Actions
        self.btn_start.clicked.connect(self.on_start_clicked)
        self.btn_stop.clicked.connect(self.presenter.stop_scan)
        self.btn_pause.clicked.connect(self.presenter.pause_scan)
        self.btn_resume.clicked.connect(self.presenter.resume_scan)
        
        # Presenter Signals
        self.presenter.scan_started.connect(self.on_scan_started)
        self.presenter.scan_completed.connect(self.on_scan_completed)
        self.presenter.scan_failed.connect(self.on_scan_failed)
        
    def on_start_clicked(self):
        params = {
            "x_min": self.input_x_min.text(),
            "x_max": self.input_x_max.text(),
            "x_nb_points": self.input_x_nb.text(),
            "y_min": self.input_y_min.text(),
            "y_max": self.input_y_max.text(),
            "y_nb_points": self.input_y_nb.text(),
            "motion_speed_mm_s": self.input_speed.text(),
            "scan_pattern": self.combo_pattern.currentText(),
            # Export-related parameters
            "export_enabled": self.checkbox_export_enabled.isChecked(),
            "export_output_directory": self.input_export_directory.text(),
            "export_filename_base": self.input_export_filename.text(),
            "export_format": self.combo_export_format.currentText(),
        }

        self.presenter.start_scan(params)
        
    def on_scan_started(self, scan_id, config):
        self.lbl_status.setText(f"Status: Running (ID: {scan_id})")
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_pause.setEnabled(True)
        self.btn_resume.setEnabled(False)
        
    def on_scan_completed(self, scan_id, total):
        self.lbl_status.setText(f"Status: Completed ({total} points)")
        self.reset_buttons()
        
    def on_scan_failed(self, scan_id, reason):
        self.lbl_status.setText(f"Status: Failed ({reason})")
        self.reset_buttons()
        
    def reset_buttons(self):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_pause.setEnabled(False)
        self.btn_resume.setEnabled(False)
