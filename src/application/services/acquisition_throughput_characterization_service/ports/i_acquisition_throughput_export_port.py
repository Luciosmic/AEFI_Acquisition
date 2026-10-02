from abc import ABC, abstractmethod
from typing import Sequence

from application.services.acquisition_throughput_characterization_service.dtos.acquisition_throughput_dtos import (
    AcquisitionThroughputCharacterizationDTO,
    AcquisitionThroughputSampleDTO,
)
from domain.shared_kernel.operation_result import OperationResult


class IAcquisitionThroughputExportPort(ABC):
    """
    Responsibility:
    - Persist one throughput characterization: raw samples + summary.

    Rationale:
    - The 2024 characterization was lost because it lived in an ad hoc
      spreadsheet; the raw samples must be kept next to the summary so the
      analysis can be redone.

    Design:
    - Returns the written location, or a failure (disk full, no permission)
      — never raises for an expected I/O failure.
    """

    @abstractmethod
    def export(
        self,
        result: AcquisitionThroughputCharacterizationDTO,
        samples: Sequence[AcquisitionThroughputSampleDTO],
    ) -> OperationResult[str, str]: ...
