from abc import ABC, abstractmethod

from application.services.frequency_sweep_service.dtos.frequency_sweep_dtos import (
    FrequencyPointDTO,
    FrequencySweepResultDTO,
)


class IFrequencySweepOutputPort(ABC):
    """
    Output Port for FrequencySweepService — see
    i_frequency_sweep_output_port_intention.md.

    Called from the sweep's background task: implementations must be
    thread-safe (Qt signals are).
    """

    @abstractmethod
    def present_frequency_sweep_step(self, message: str) -> None: ...

    @abstractmethod
    def present_frequency_point_measured(self, point: FrequencyPointDTO) -> None: ...

    @abstractmethod
    def present_frequency_sweep_ended(self, result: FrequencySweepResultDTO) -> None:
        """Completed or cancelled: what was acquired, and where it was exported."""

    @abstractmethod
    def present_frequency_sweep_failed(self, reason: str) -> None: ...
