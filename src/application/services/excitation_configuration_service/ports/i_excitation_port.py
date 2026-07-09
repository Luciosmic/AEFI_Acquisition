from abc import ABC, abstractmethod
from domain.value_objects.excitation.excitation_parameters import ExcitationParameters

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
