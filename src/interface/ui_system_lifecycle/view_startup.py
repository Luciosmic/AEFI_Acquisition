"""
Startup View for Interface V2.

Responsibility:
- Displays splash screen for the whole app composition (software + hardware)
- Waits for SystemLifecyclePresenter to complete hardware startup

Rationale:
- Provides user feedback from the very first moment of the app, not just
  during hardware initialization
- Blocks UI until hardware is ready
- Adapted from interface V1 for PySide6 compatibility
"""

from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt

from interface.ui_system_lifecycle.presenter_system_lifecycle import SystemLifecyclePresenter
from application.services.system_lifecycle_service.system_lifecycle_service import StartupConfig
from interface.widgets.panels.logs_panel import LogsPanel

class StartupView(QDialog):
    """
    Splash screen shown for the entire app startup (software composition
    then hardware init). The caller decides when hardware init begins by
    calling start_hardware_init() once composition is done.
    """

    def __init__(self, presenter: SystemLifecyclePresenter, logs_panel: LogsPanel = None):
        super().__init__()
        self._presenter = presenter
        self.setWindowTitle("System Initialization")
        self.setFixedSize(480, 420)
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

        if logs_panel is not None:
            layout.addWidget(logs_panel, 1)

        self.setLayout(layout)

        # Connect Signals
        self._presenter.initialization_step_updated.connect(self._on_step_updated)
        self._presenter.startup_finished.connect(self._on_startup_finished)
        self._presenter.error_occurred.connect(self._on_error)

    def set_phase(self, text: str) -> None:
        """Called directly by the composition root while it builds software
        components, before hardware init (and its own step signals) starts."""
        self.status_label.setText(text)

    def start_hardware_init(self) -> None:
        """Trigger hardware startup. Call once software composition is done."""
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

