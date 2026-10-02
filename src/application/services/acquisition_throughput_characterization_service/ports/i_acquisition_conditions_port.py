from abc import ABC, abstractmethod

from application.services.acquisition_throughput_characterization_service.dtos.acquisition_parameters_dtos import (
    AcquisitionConditionsDTO,
    BenchPositionDTO,
)
from domain.shared_kernel.operation_result import OperationResult


class IAcquisitionConditionsPort(ABC):
    """
    Responsibility:
    - Read the hardware conditions a measurement is made under: mounted
      components and their characterization, ADC and AD9106 settings as
      applied, synchronous detection state, sensor mounting and applied
      rotation, host <-> MCU serial link, real/simulated backends, and the
      bench position.

    Rationale:
    - These facts live in the component catalog, controller memories, config
      files and other services; without this port the throughput service
      would depend on all of them (and their storage) to fill one document.

    Design:
    - Never raises: a fact that cannot be read is None in the DTO with its
      reason in `unknown` (or a failed OperationResult for the position).
    - Called while the sweep runs (excitation already cut), so the AD9106
      settings are those applied during the measurement.
    - The bench position is a separate query: read at the start and at the
      end of the sweep (the motors are not held by it).
    """

    @abstractmethod
    def read_conditions(self) -> AcquisitionConditionsDTO: ...

    @abstractmethod
    def read_bench_position(self) -> OperationResult[BenchPositionDTO, str]: ...
