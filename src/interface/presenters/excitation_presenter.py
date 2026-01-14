"""
Excitation Configuration Presenter - Interface V2

Bridges between ExcitationConfigurationService and ExcitationPanel.
Adapted from interface v1 for PySide6.
"""

from PySide6.QtCore import QObject, Signal, Slot
from application.services.excitation_configuration_service.excitation_configuration_service import ExcitationConfigurationService
from domain.value_objects.excitation.excitation_mode import ExcitationMode
from domain.value_objects.excitation.excitation_parameters import ExcitationParameters


class ExcitationPresenter(QObject):
    """
    Presenter for the Excitation Configuration Panel.
    - Receives UI events and calls Service
    - Emits signals for UI updates
    """

    # Signals emitted to the UI
    excitation_updated = Signal(str, float, float)  # mode_name, level_percent, frequency
    excitation_error = Signal(str)  # error_message

    def __init__(self, service: ExcitationConfigurationService):
        super().__init__()
        self._service = service

    @Slot(str, float, float)
    def on_excitation_changed(self, mode_code: str, level_percent: float, frequency: float):
        """
        Handle excitation change from panel.
        
        Args:
            mode_code: Mode code string (X_DIR, Y_DIR, CIRCULAR_PLUS, etc.)
            level_percent: Level (0.0 - 100.0)
            frequency: Frequency in Hz
        """
        try:
            # Convert mode code to ExcitationMode enum
            mode = self._code_to_mode(mode_code)
            
            # Call service
            self._service.set_excitation(mode, level_percent, frequency)
            
            # Emit signal for UI confirmation
            self.excitation_updated.emit(mode_code, level_percent, frequency)
            
        except Exception as e:
            error_msg = f"Failed to set excitation: {str(e)}"
            print(f"[ExcitationPresenter] ERROR: {error_msg}")
            self.excitation_error.emit(error_msg)

    def get_current_parameters(self) -> ExcitationParameters:
        """Get current excitation parameters from service."""
        return self._service.get_current_parameters()

    def _code_to_mode(self, code: str) -> ExcitationMode:
        """Convert mode code string to ExcitationMode enum."""
        mapping = {
            "X_DIR": ExcitationMode.X_DIR,
            "Y_DIR": ExcitationMode.Y_DIR,
            "CIRCULAR_PLUS": ExcitationMode.CIRCULAR_PLUS,
            "CIRCULAR_MINUS": ExcitationMode.CIRCULAR_MINUS,
            "CUSTOM": ExcitationMode.CUSTOM
        }
        return mapping.get(code, ExcitationMode.X_DIR)
