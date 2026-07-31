from abc import ABC, abstractmethod
from domain.shared_kernel.excitation.value_objects.excitation_parameters import ExcitationParameters

class IExcitationPort(ABC):
    """
    Port for controlling the excitation generation.
    """

    @abstractmethod
    def apply_excitation(self, params: ExcitationParameters) -> None:
        """
        Apply the requested excitation parameters (Mode and Level) to the hardware.
        """
        raise NotImplementedError

    @abstractmethod
    def set_gain(self, level_s1_s2_percent: float, level_s3_s4_percent: float) -> None:
        """
        Write only the gain, leaving mode/phase/frequency untouched and
        without publishing a config-changed event — for the
        differential-scan mute/unmute cycle, a transient per-point toggle
        that shouldn't sync the Hardware Config tab on every point.
        """
        raise NotImplementedError
