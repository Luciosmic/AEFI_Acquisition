"""
Startup View for Interface V2.

Responsibility:
- Displays splash screen for the whole app composition (software + hardware)
- Waits for SystemLifecyclePresenter to complete hardware startup
- Shows only the loading bar (with the application's icon) until a log line
  is written; then grows to show the logs and their Debug / Warning boxes

Rationale:
- Provides user feedback from the very first moment of the app, not just
  during hardware initialization
- Blocks UI until hardware is ready
- Adapted from interface V1 for PySide6 compatibility
"""

from PySide6.QtWidgets import QApplication, QDialog, QHBoxLayout, QVBoxLayout, QLabel, QPlainTextEdit, QProgressBar, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from interface.ui_system_lifecycle.presenter_system_lifecycle import SystemLifecyclePresenter
from application.shared.system_lifecycle_service.system_lifecycle_service import StartupConfig
from interface.widgets.panels.logs_panel import LogsPanel

class StartupView(QDialog):
    """
    Splash screen shown for the entire app startup (software composition
    then hardware init). The caller decides when hardware init begins by
    calling start_hardware_init() once composition is done.
    """

    COMPACT_SIZE = (480, 90)  # loading bar only
    EXPANDED_SIZE = (480, 420)  # once logs are written, or on a failure

    def __init__(self, presenter: SystemLifecyclePresenter, logs_panel: LogsPanel = None, icon: QIcon = None):
        super().__init__()
        self._presenter = presenter
        self.setWindowTitle("System Initialization")
        self.setFixedSize(*self.COMPACT_SIZE)
        self.setWindowFlags(Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint)
        self.setModal(True)

        # UI Setup
        layout = QVBoxLayout()

        # The application's own icon, next to the status and the loading bar.
        top_row = QHBoxLayout()
        self.icon_label = QLabel()
        if icon is not None and not icon.isNull():
            self.setWindowIcon(icon)
            self.icon_label.setPixmap(icon.pixmap(48, 48))
        else:
            self.icon_label.hide()
        top_row.addWidget(self.icon_label)
        status_column = QVBoxLayout()

        self.status_label = QLabel("Starting system...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_column.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate mode by default
        self.progress_bar.setTextVisible(False)
        status_column.addWidget(self.progress_bar)
        top_row.addLayout(status_column, 1)
        layout.addLayout(top_row)

        # Hidden until a startup failure: details + manual close (no auto-close).
        self.failure_details = QPlainTextEdit()
        self.failure_details.setReadOnly(True)
        self.failure_details.hide()
        layout.addWidget(self.failure_details, 1)

        self.close_button = QPushButton("Fermer")
        self.close_button.clicked.connect(lambda: QApplication.exit(1))
        self.close_button.hide()
        layout.addWidget(self.close_button)

        # Hidden until its first line: only the loading bar shows before anything is logged.
        self._logs_panel = logs_panel
        if logs_panel is not None:
            logs_panel.hide()
            layout.addWidget(logs_panel, 1)
            logs_panel.text_edit.textChanged.connect(self._on_logs_written)

        self.setLayout(layout)

        # Connect Signals
        self._presenter.initialization_step_updated.connect(self._on_step_updated)
        self._presenter.startup_finished.connect(self._on_startup_finished)
        self._presenter.error_occurred.connect(self._on_error)

    def set_phase(self, text: str) -> None:
        """Called directly by the composition root while it builds software
        components, before hardware init (and its own step signals) starts."""
        self.status_label.setText(text)

    def show_failure(self, details: str) -> None:
        """Keep the splash open on a startup failure: show the details and let
        the operator quit (non-zero exit code) with the "Fermer" button."""
        self.status_label.setText("Échec du démarrage")
        self.progress_bar.hide()
        self.failure_details.setPlainText(details)
        self.failure_details.show()
        self._expand()
        self.close_button.show()
        if not self.isVisible():
            self.show()

    def _on_logs_written(self) -> None:
        if self._logs_panel.text_edit.document().isEmpty():
            return
        self._logs_panel.text_edit.textChanged.disconnect(self._on_logs_written)
        self._logs_panel.show()
        self._expand()

    def _expand(self) -> None:
        """Grow to the expanded size around the same centre: the splash stays where the operator sees it."""
        if self.size().toTuple() == self.EXPANDED_SIZE:
            return
        centre = self.geometry().center()
        self.setFixedSize(*self.EXPANDED_SIZE)
        geometry = self.geometry()
        geometry.moveCenter(centre)
        self.move(geometry.topLeft())

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
            self.show_failure(f"Initialization Failed: {'; '.join(errors)}")

    def _on_error(self, message: str):
        self.status_label.setText(f"Error: {message}")

