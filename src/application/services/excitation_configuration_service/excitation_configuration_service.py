from .i_excitation_port import IExcitationPort
from domain.value_objects.excitation.excitation_parameters import ExcitationParameters
from domain.value_objects.excitation.excitation_level import ExcitationLevel
from domain.value_objects.excitation.excitation_mode import ExcitationMode

class ExcitationConfigurationService:
    """
    Application Service to configure the field excitation.
    """

    def __init__(self, excitation_port: IExcitationPort) -> None:
        self._port = excitation_port
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
        
        self._port.apply_excitation(params)
        self._current_params = params

    def get_current_parameters(self) -> ExcitationParameters:
        return self._current_params
