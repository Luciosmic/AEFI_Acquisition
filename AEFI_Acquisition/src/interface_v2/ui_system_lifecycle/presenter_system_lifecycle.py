"""
System Lifecycle Presenter for Interface V2.

Responsibility:
- Handles startup/shutdown sequencing in a background thread
- Emits signals for UI updates (thread-safe)
- Implements ISystemLifecycleOutputPort

Rationale:
- Separates UI concerns from business logic
- Provides thread-safe communication between services and UI
- Adapted from interface V1 for PySide6 compatibility
"""

from PySide6.QtCore import QObject, Signal
from typing import List, Optional
import threading

from application.services.system_lifecycle_service.i_system_lifecycle_output_port import ISystemLifecycleOutputPort
from application.services.system_lifecycle_service.system_lifecycle_service import (
    SystemStartupApplicationService, 
    SystemShutdownApplicationService,
    StartupConfig,
    ShutdownConfig
)

from abc import ABCMeta

# Fix for metaclass conflict between QObject and ABC
class QABCMeta(type(QObject), ABCMeta):
    pass

class SystemLifecyclePresenter(QObject, ISystemLifecycleOutputPort, metaclass=QABCMeta):
    """
    Presenter for System Lifecycle.
    Handles startup/shutdown sequencing in a background thread and emits signals for UI updates.
    """
    
    # Signals (PySide6 uses Signal instead of pyqtSignal)
    startup_started = Signal(str)
    initialization_step_updated = Signal(str, str)  # step, status
    startup_finished = Signal(bool, list)  # success, errors
    
    shutdown_started = Signal()
    shutdown_step_updated = Signal(str, str)
    shutdown_finished = Signal(bool, list)
    
    error_occurred = Signal(str)

    def __init__(self):
        super().__init__()
        self._startup_service: Optional[SystemStartupApplicationService] = None
        self._shutdown_service: Optional[SystemShutdownApplicationService] = None

    def set_services(self, 
                     startup_service: SystemStartupApplicationService, 
                     shutdown_service: SystemShutdownApplicationService):
        """Dependency Injection after initialization."""
        self._startup_service = startup_service
        self._shutdown_service = shutdown_service

    # --- Command Methods (Called by UI) ---

    def start_system_startup(self, config: StartupConfig):
        """Starts the system startup process in a background thread."""
        if not self._startup_service:
            self.present_error("Startup Service not initialized.")
            return
            
        thread = threading.Thread(target=self._run_startup, args=(config,))
        thread.daemon = True
        thread.start()

    def start_system_shutdown(self, config: ShutdownConfig):
        """Starts the system shutdown process in a background thread."""
        if not self._shutdown_service:
            self.present_error("Shutdown Service not initialized.")
            return

        thread = threading.Thread(target=self._run_shutdown, args=(config,))
        thread.daemon = True
        thread.start()

    # --- Internal Background Execution ---

    def _run_startup(self, config: StartupConfig):
        # Service calls are synchronous
        self._startup_service.startup_system(config)

    def _run_shutdown(self, config: ShutdownConfig):
        self._shutdown_service.shutdown_system(config)

    # --- ISystemLifecycleOutputPort Implementation (Thread-Safe Signals) ---

    def present_startup_started(self, config_summary: str) -> None:
        self.startup_started.emit(config_summary)

    def present_initialization_step(self, step_name: str, status: str) -> None:
        self.initialization_step_updated.emit(step_name, status)

    def present_startup_completed(self, success: bool, errors: List[str]) -> None:
        self.startup_finished.emit(success, errors)

    def present_shutdown_started(self) -> None:
        self.shutdown_started.emit()

    def present_shutdown_step(self, step_name: str, status: str) -> None:
        self.shutdown_step_updated.emit(step_name, status)

    def present_shutdown_completed(self, success: bool, errors: List[str]) -> None:
        self.shutdown_finished.emit(success, errors)

    def present_error(self, error_message: str) -> None:
        self.error_occurred.emit(error_message)

