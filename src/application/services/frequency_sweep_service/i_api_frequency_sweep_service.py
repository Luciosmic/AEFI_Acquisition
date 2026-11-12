from abc import ABC, abstractmethod

from application.services.frequency_sweep_service.dtos.frequency_sweep_dtos import FrequencySweepRequestDTO
from application.services.frequency_sweep_service.ports.i_frequency_sweep_output_port import IFrequencySweepOutputPort


class IApiFrequencySweepService(ABC):
    """
    Responsibility:
    - Inbound API contract for FrequencySweepService (presenter -> application).

    Design:
    - Pure ABC. The outcome of start_sweep() arrives through the output port
      (the sweep runs in the background).
    """

    @abstractmethod
    def set_output_port(self, output_port: IFrequencySweepOutputPort) -> None: ...

    @abstractmethod
    def start_sweep(self, request: FrequencySweepRequestDTO) -> None: ...

    @abstractmethod
    def stop_sweep(self) -> None:
        """Stop after the frequency being acquired; what was acquired is exported."""
