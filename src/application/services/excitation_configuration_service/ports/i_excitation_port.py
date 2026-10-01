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

    @abstractmethod
    def set_link_dds1_dds2(self, linked: bool) -> None:
        """
        Persist and publish the DDS1/DDS2 gain link preference (Excitation
        panel's "Link S1-S2 = S3-S4") so the Hardware Advanced Config tab's
        own link_dds1_dds2 parameter stays in sync with it, and vice versa.
        """
        raise NotImplementedError
