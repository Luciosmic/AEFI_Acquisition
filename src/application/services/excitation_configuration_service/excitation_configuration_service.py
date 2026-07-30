from .ports.i_excitation_port import IExcitationPort
from domain.shared_kernel.value_objects.excitation.excitation_parameters import ExcitationParameters
from domain.shared_kernel.value_objects.excitation.excitation_level import ExcitationLevel
from domain.shared_kernel.value_objects.excitation.excitation_mode import ExcitationMode
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus
from domain.shared_kernel.events.excitation_frequency_changed.excitation_frequency_changed import (
    ExcitationFrequencyChanged,
)

EXCITATION_FREQUENCY_CHANGED_TOPIC = "excitationfrequencychanged"

class ExcitationConfigurationService:
    """
    Application Service to configure the field excitation.
    """

    def __init__(self, excitation_port: IExcitationPort, event_bus: IDomainEventBus) -> None:
        self._port = excitation_port
        self._event_bus = event_bus
        self._current_params = ExcitationParameters.off()

    def set_excitation(self, mode: ExcitationMode, level_percent: float, frequency: float) -> None:
        """
        Set the excitation mode, level, and frequency.

        Args:
            mode: Desired ExcitationMode
            level_percent: Intensity (0.0 - 100.0)
            frequency: Frequency logic (Hz)
        """
        level = ExcitationLevel(level_percent)
        params = ExcitationParameters(mode, level, frequency)

        frequency_changed = frequency != self._current_params.frequency

        self._port.apply_excitation(params)
        self._current_params = params

        if frequency_changed:
            self._event_bus.publish(
                EXCITATION_FREQUENCY_CHANGED_TOPIC,
                ExcitationFrequencyChanged(frequency_hz=frequency),
            )

    def get_current_parameters(self) -> ExcitationParameters:
        return self._current_params
