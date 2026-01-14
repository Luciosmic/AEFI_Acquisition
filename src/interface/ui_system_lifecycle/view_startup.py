"""
Startup View for Interface V2.

Responsibility:
- Displays splash screen during system initialization
- Waits for SystemLifecyclePresenter to complete startup
- Auto-starts initialization sequence

Rationale:
- Provides user feedback during hardware initialization
- Blocks UI until hardware is ready
- Adapted from interface V1 for PySide6 compatibility
"""

from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt, QTimer

from interface.ui_system_lifecycle.presenter_system_lifecycle import SystemLifecyclePresenter
from application.services.system_lifecycle_service.system_lifecycle_service import StartupConfig

class StartupView(QDialog):
    """
    Splash screen displayed during system initialization.
    Waits for the SystemLifecyclePresenter to complete startup.
    """
    
    def __init__(self, presenter: SystemLifecyclePresenter):
        super().__init__()
        self._presenter = presenter
        self.setWindowTitle("System Initialization")
        self.setFixedSize(400, 150)
        self.setWindowFlags(Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint)
        self.setModal(True)
        
        # UI Setup
        layout = QVBoxLayout()
        
        self.status_label = QLabel("Starting system...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate mode by default
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.setLayout(layout)
        
        # Connect Signals
        self._presenter.initialization_step_updated.connect(self._on_step_updated)
        self._presenter.startup_finished.connect(self._on_startup_finished)
        self._presenter.error_occurred.connect(self._on_error)
        
        # Auto-start after show
        QTimer.singleShot(100, self._start_initialization)

    def _start_initialization(self):
        # Trigger the actual startup logic
        config = StartupConfig(verify_hardware=True, load_last_calibration=False)
        self._presenter.start_system_startup(config)

    def _on_step_updated(self, step: str, status: str):
        self.status_label.setText(f"{step}: {status}")

    def _on_startup_finished(self, success: bool, errors: list):
        if success:
            self.status_label.setText("Initialization Complete!")
            self.accept()  # Close dialog with QDialog.Accepted
        else:
            self.status_label.setText(f"Initialization Failed: {'; '.join(errors)}")
            # We might want to keep it open or reject
            # For now, let's reject to signal Main to exit or show error
            self.reject()

    def _on_error(self, message: str):
        self.status_label.setText(f"Error: {message}")

