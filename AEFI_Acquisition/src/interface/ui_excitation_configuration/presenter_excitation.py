"""
Excitation Configuration Presenter - Interface Layer

Responsibility:
- Bridge between ExcitationConfigurationService (Application) and ExcitationWidget (UI)
- Handle user interactions and emit Qt signals for UI updates
- Translate UI events to service calls

Rationale:
- Separates UI from application logic
- Enables testability (presenter can be tested without UI)
- Follows MVP pattern
"""

from PyQt6.QtCore import QObject, pyqtSignal
from application.services.excitation_configuration_service.excitation_configuration_service import ExcitationConfigurationService
from domain.value_objects.excitation.excitation_mode import ExcitationMode
from domain.value_objects.excitation.excitation_parameters import ExcitationParameters


class ExcitationPresenter(QObject):
    """
    Presenter for the Excitation Configuration UI.
    Receives UI events and calls Service.
    Receives Service updates and emits Qt signals.
    """

    # Signals emitted to the UI
    excitation_updated = pyqtSignal(str, float, float)  # mode_name, level_percent, frequency
    excitation_error = pyqtSignal(str)  # error_message

    def __init__(self, service: ExcitationConfigurationService):
        """
        Initialize the presenter.
        
        Args:
            service: ExcitationConfigurationService instance
        """
        super().__init__()
        self._service = service

    def set_excitation(self, mode: ExcitationMode, level_percent: float, frequency: float) -> None:
        """
        Set excitation parameters from UI.
        
        Args:
            mode: ExcitationMode enum value
            level_percent: Level (0.0 - 100.0)
            frequency: Frequency in Hz
        """
        try:
            self._service.set_excitation(mode, level_percent, frequency)
            
            # Emit signal for UI update
            mode_name = mode.name
            self.excitation_updated.emit(mode_name, level_percent, frequency)
            
        except Exception as e:
            error_msg = f"Failed to set excitation: {str(e)}"
            self.excitation_error.emit(error_msg)

    def get_current_parameters(self) -> ExcitationParameters:
        """Get current excitation parameters."""
        return self._service.get_current_parameters()
