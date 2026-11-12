from abc import ABC, abstractmethod
from typing import Sequence, Tuple

from application.services.frequency_sweep_service.dtos.acquisition_parameters_dtos import (
    FrequencySweepAcquisitionParametersDTO,
)
from application.services.frequency_sweep_service.dtos.frequency_sweep_dtos import (
    FrequencySweepResultDTO,
    FrequencySweepSampleDTO,
)
from application.shared.acquisition_parameters.acquisition_conditions_dtos import ExportedFileDTO
from domain.shared_kernel.operation_result import OperationResult


class IFrequencySweepExportPort(ABC):
    """
    Persist one frequency sweep in its own export location: the response per
    frequency, the raw samples, and the acquisition parameters — see
    i_frequency_sweep_export_port_intention.md.

    Expected I/O failures (disk full, no permission) are failures, never raised.
    """

    @abstractmethod
    def open_export(self, role: str, table_height_mm: float) -> OperationResult[str, str]:
        """Create the export location; returns it."""

    @abstractmethod
    def export(
        self, location: str, result: FrequencySweepResultDTO, samples: Sequence[FrequencySweepSampleDTO]
    ) -> OperationResult[Tuple[ExportedFileDTO, ...], str]: ...

    @abstractmethod
    def write_acquisition_parameters(
        self, location: str, parameters: FrequencySweepAcquisitionParametersDTO
    ) -> OperationResult[None, str]:
        """(Re)write the acquisition parameters of the sweep in `location`."""
