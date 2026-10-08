from abc import ABC, abstractmethod

from application.services.acquisition_throughput_characterization_service.dtos.acquisition_throughput_dtos import (
    AcquisitionThroughputCharacterizationDTO,
    AcquisitionThroughputPointDTO,
)


class IAcquisitionThroughputOutputPort(ABC):
    """
    Output Port for AcquisitionThroughputCharacterizationService — see
    i_acquisition_throughput_output_port_intention.md.

    Called from the sweep's background task: implementations must be
    thread-safe (Qt signals are).
    """

    @abstractmethod
    def present_throughput_characterization_step(self, message: str) -> None: ...

    @abstractmethod
    def present_throughput_point_measured(self, point: AcquisitionThroughputPointDTO) -> None: ...

    @abstractmethod
    def present_throughput_characterization_succeeded(self, result: AcquisitionThroughputCharacterizationDTO) -> None: ...

    @abstractmethod
    def present_throughput_characterization_failed(self, reason: str) -> None: ...
