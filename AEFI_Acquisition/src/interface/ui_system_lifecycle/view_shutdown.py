from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt, QTimer

from interface.ui_system_lifecycle.presenter_system_lifecycle import SystemLifecyclePresenter
from application.services.system_lifecycle_service.system_lifecycle_service import ShutdownConfig

class ShutdownView(QDialog):
    """
    Window displayed during system shutdown.
    Waits for the SystemLifecyclePresenter to complete shutdown.
    """
    
    def __init__(self, presenter: SystemLifecyclePresenter):
        super().__init__()
        self._presenter = presenter
        self.setWindowTitle("System Shutdown")
        self.setFixedSize(400, 150)
        # Use Tool | Frameless to look like a system modal
        self.setWindowFlags(Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint)
        self.setModal(True)
        
        # UI Setup
        layout = QVBoxLayout()
        
        self.status_label = QLabel("Shutting down system...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0) # Indeterminate mode
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.setLayout(layout)
        
        # Connect Signals
        self._presenter.shutdown_step_updated.connect(self._on_step_updated)
        self._presenter.shutdown_finished.connect(self._on_shutdown_finished)
        self._presenter.error_occurred.connect(self._on_error)
        
        # Auto-start after show
        QTimer.singleShot(100, self._start_shutdown)

    def _start_shutdown(self):
        # Trigger the actual shutdown logic
        config = ShutdownConfig(save_state=True)
        self._presenter.start_system_shutdown(config)

    def _on_step_updated(self, step: str, status: str):
        self.status_label.setText(f"{step}: {status}")

    def _on_shutdown_finished(self, success: bool, errors: list):
        if success:
            self.status_label.setText("Shutdown Complete. Goodbye!")
            # Delay slightly to let user read message
            QTimer.singleShot(1000, self.accept)
        else:
            self.status_label.setText(f"Shutdown Finished with Errors: {'; '.join(errors)}")
            # Even if errors, we probably want to close
            QTimer.singleShot(2000, self.reject)

    def _on_error(self, message: str):
        self.status_label.setText(f"Error: {message}")
