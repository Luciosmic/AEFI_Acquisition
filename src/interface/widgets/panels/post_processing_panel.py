from PySide6.QtWidgets import QLabel, QPushButton, QMessageBox
from PySide6.QtCore import QProcess
import os
import sys

from interface.widgets.panels.base_panel import BasePanel

class PostProcessingPanel(BasePanel):
    """Panel dedicated to launching and monitoring the post-processing module."""
    def __init__(self, parent=None):
        super().__init__("Post-Processing", "#8E24AA", parent) # Purple theme
        
        self.process = None # Using QProcess to monitor state, keeping it alive

        # Description
        desc_label = QLabel("Run the post-processing pipeline on scanned data and launch visualization.")
        desc_label.setWordWrap(True)
        self.layout.addWidget(desc_label)
        
        # Launch Button
        self.btn_launch = QPushButton("Launch Post-Processing && Visualisation")
        self.btn_launch.setStyleSheet("""
            QPushButton {
                background-color: #1976D2;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565C0;
            }
            QPushButton:disabled {
                background-color: #78909C;
                color: #CFD8DC;
            }
        """)
        self.btn_launch.clicked.connect(self._launch_post_processor)
        self.layout.addWidget(self.btn_launch)
        
        # Status Label
        self.status_label = QLabel("Status: Ready")
        self.status_label.setStyleSheet("color: #AAA; font-style: italic;")
        self.layout.addWidget(self.status_label)
        
        self.layout.addStretch()

    def _launch_post_processor(self):
        if self.process is not None and self.process.state() == QProcess.Running:
            QMessageBox.information(self, "Already Running", "The Post-Processing module is already running!")
            return

        python_exe = sys.executable
        # From src/interface/widgets/panels/post_processing_panel.py -> src/interface/widgets/panels -> src/interface/widgets -> src/interface -> src -> root
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        script_path = os.path.join(
            root_dir, "external_modules", "post_processor_module", "composition_root.py"
        )
        
        print(f"[PostProcessingPanel] Launching Post-Processor: {python_exe} {script_path}")
        
        self.process = QProcess(self)
        self.process.finished.connect(self._on_process_finished)
        self.process.errorOccurred.connect(self._on_process_error)
        
        self.status_label.setText("Status: Running...")
        self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        self.btn_launch.setText("Post-Processing is Running...")
        self.btn_launch.setEnabled(False)
        
        # Start detached or as a child process? 
        # The user said "le subprocess doit tout le temps tourner même si on réduit l'onglet".
        # A standard QProcess with the panel as parent keeps running when the panel is hidden/minimized.
        self.process.start(python_exe, [script_path])

    def _on_process_finished(self, exitCode, exitStatus):
        print(f"[PostProcessingPanel] Post-Processor finished with code {exitCode}")
        self.status_label.setText(f"Status: Finished (code {exitCode})")
        self.status_label.setStyleSheet("color: #AAA;")
        self.btn_launch.setText("Launch Post-Processing && Visualisation")
        self.btn_launch.setEnabled(True)

    def _on_process_error(self, error):
        print(f"[PostProcessingPanel] QProcess error: {error}")
        self.status_label.setText(f"Status: Error ({error})")
        self.status_label.setStyleSheet("color: #F44336;")
        self.btn_launch.setText("Launch Post-Processing && Visualisation")
        self.btn_launch.setEnabled(True)
