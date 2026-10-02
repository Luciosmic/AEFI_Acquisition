from abc import ABC, abstractmethod

from application.services.acquisition_throughput_characterization_service.dtos.acquisition_throughput_dtos import (
    AcquisitionThroughputRequestDTO,
)
from application.services.acquisition_throughput_characterization_service.ports.i_acquisition_throughput_output_port import (
    IAcquisitionThroughputOutputPort,
)


class IApiAcquisitionThroughputCharacterizationService(ABC):
    """
    Responsibility:
    - Inbound API contract for AcquisitionThroughputCharacterizationService
      (presenter -> application).

    Design:
    - Pure ABC. The outcome of start_characterization() arrives through the
      output port (the sweep runs in the background).
    """

    @abstractmethod
    def set_output_port(self, output_port: IAcquisitionThroughputOutputPort) -> None: ...

    @abstractmethod
    def start_characterization(self, request: AcquisitionThroughputRequestDTO) -> None: ...
