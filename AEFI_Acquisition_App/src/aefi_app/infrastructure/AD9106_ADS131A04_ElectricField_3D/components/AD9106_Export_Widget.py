from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QHBoxLayout, QPushButton, QLabel, QLineEdit, QFileDialog
from PyQt5.QtCore import pyqtSignal, Qt

class ExportWidget(QWidget):
    start_export = pyqtSignal(dict)
    stop_export = pyqtSignal()
    config_changed = pyqtSignal(dict)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        self.export_group = QGroupBox("Export CSV : Experimental Data vs Time")
        export_layout = QVBoxLayout(self.export_group)
        btns_layout = QHBoxLayout()
        self.start_btn = QPushButton("🟢 Démarrer Export")
        self.start_btn.clicked.connect(self._emit_start_export)
        self.stop_btn = QPushButton("🔴 Arrêter Export")
        self.stop_btn.clicked.connect(self.stop_export.emit)
        btns_layout.addWidget(self.start_btn)
        btns_layout.addWidget(self.stop_btn)
        btns_layout.addStretch()
        export_layout.addLayout(btns_layout)
        config_layout = QVBoxLayout()
        config_layout.setSpacing(8)
        config_layout.setContentsMargins(0, 0, 0, 0)
        path_layout = QHBoxLayout()
        path_label = QLabel("Data Path")
        self.path_edit = QLineEdit(r"C:\Users\manip\Documents\Data")
        browse_btn = QPushButton("…")
        def browse():
            d = QFileDialog.getExistingDirectory(self, "Choisir le dossier d'export", self.path_edit.text())
            if d:
                self.path_edit.setText(d)
                self.emit_config()
        browse_btn.clicked.connect(browse)
        self.path_edit.editingFinished.connect(self.emit_config)
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(browse_btn)
        file_layout = QHBoxLayout()
        file_label = QLabel("File Name")
        self.file_edit = QLineEdit("Default")
        self.file_edit.editingFinished.connect(self.emit_config)
        file_layout.addWidget(file_label)
        file_layout.addWidget(self.file_edit)
        config_layout.addLayout(path_layout)
        config_layout.addLayout(file_layout)
        export_layout.addLayout(config_layout)
        layout.addWidget(self.export_group)
        self.export_status_label = QLabel("Export: ARRÊTÉ")
        self.export_status_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(self.export_status_label)
    def _emit_start_export(self):
        self.start_export.emit(self.get_config())
    def get_config(self):
        return {
            'output_dir': self.path_edit.text().strip(),
            'filename_base': self.file_edit.text().strip(),
        }
    def emit_config(self):
        self.config_changed.emit(self.get_config())
    def set_export_status(self, status: str):
        self.export_status_label.setText(f"Export: {status}")
    def set_enabled(self, enabled: bool):
        self.start_btn.setEnabled(enabled)
        self.stop_btn.setEnabled(True)
        self.path_edit.setEnabled(enabled)
        self.file_edit.setEnabled(enabled) 