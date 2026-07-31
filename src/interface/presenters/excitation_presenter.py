"""
Excitation Configuration Presenter - Interface V2

Bridges between ExcitationConfigurationService and ExcitationPanel.
Adapted from interface v1 for PySide6.
"""

from PySide6.QtCore import QObject, Signal, Slot
from application.services.excitation_configuration_service.excitation_configuration_service import (
    ExcitationConfigurationService,
    EXCITATION_FREQUENCY_CHANGED_TOPIC,
    DDS_CHANNEL_CONFIG_CHANGED_TOPIC,
)
from domain.shared_kernel.excitation.value_objects.excitation_mode import ExcitationMode
from domain.shared_kernel.excitation.value_objects.excitation_parameters import ExcitationParameters
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus


class ExcitationPresenter(QObject):
    """
    Presenter for the Excitation Configuration Panel.
    - Receives UI events and calls Service
    - Emits signals for UI updates
    """

    # Signals emitted to the UI
    excitation_updated = Signal(str, float, float, float)  # mode_name, level_s1_s2_percent, level_s3_s4_percent, frequency
    excitation_error = Signal(str)  # error_message

    def __init__(self, service: ExcitationConfigurationService, event_bus: IDomainEventBus):
        super().__init__()
        self._service = service
        # The Hardware Config tab can change frequency, or channel 1/2
        # gain/phase, directly on the shared DDS — refresh this panel's
        # display when that happens instead of going stale. The service
        # itself (subscribed before this presenter — see main.py
        # construction order) has already recomputed mode/level by the time
        # this handler runs.
        event_bus.subscribe(EXCITATION_FREQUENCY_CHANGED_TOPIC, self._on_hardware_config_changed)
        event_bus.subscribe(DDS_CHANNEL_CONFIG_CHANGED_TOPIC, self._on_hardware_config_changed)

    def _on_hardware_config_changed(self, event) -> None:
        self.refresh_state()

    def refresh_state(self) -> None:
        """Push the service's current parameters to the UI (startup + external changes)."""
        params = self._service.get_current_parameters()
        self.excitation_updated.emit(
            params.mode.name, params.level_s1_s2.value, params.level_s3_s4.value, params.frequency
        )

    @Slot(str, float, float, float)
    def on_excitation_changed(
        self, mode_code: str, level_s1_s2_percent: float, level_s3_s4_percent: float, frequency: float
    ):
        """
        Handle excitation change from panel.

        Args:
            mode_code: Mode code string (X_DIR, Y_DIR, CIRCULAR_PLUS, etc.)
            level_s1_s2_percent: Level of spheres S1/S2, DDS2 generator (0.0 - 100.0)
            level_s3_s4_percent: Level of spheres S3/S4, DDS1 generator (0.0 - 100.0)
            frequency: Frequency in Hz
        """
        try:
            # Convert mode code to ExcitationMode enum
            mode = self._code_to_mode(mode_code)

            # Call service
            self._service.set_excitation(mode, level_s1_s2_percent, level_s3_s4_percent, frequency)

            # Emit signal for UI confirmation
            self.excitation_updated.emit(mode_code, level_s1_s2_percent, level_s3_s4_percent, frequency)

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
