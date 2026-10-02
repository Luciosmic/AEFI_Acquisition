"""
Fake Acquisition Throughput Export Port

See fake_acquisition_throughput_export_port_intention.md.
"""

from typing import List, Optional, Sequence, Tuple

from application.services.acquisition_throughput_characterization_service.dtos.acquisition_throughput_dtos import (
    AcquisitionThroughputCharacterizationDTO,
    AcquisitionThroughputSampleDTO,
)
from application.services.acquisition_throughput_characterization_service.ports.i_acquisition_throughput_export_port import (
    IAcquisitionThroughputExportPort,
)
from domain.shared_kernel.operation_result import OperationResult


class FakeAcquisitionThroughputExportPort(IAcquisitionThroughputExportPort):
    """Keeps every export in memory; `fail=True` reproduces a write failure."""

    LOCATION = "memory://acquisition_throughput"

    def __init__(self, fail: bool = False) -> None:
        self._fail = fail
        self.exports: List[Tuple[AcquisitionThroughputCharacterizationDTO, Tuple[AcquisitionThroughputSampleDTO, ...]]] = []

    def export(
        self,
        result: AcquisitionThroughputCharacterizationDTO,
        samples: Sequence[AcquisitionThroughputSampleDTO],
    ) -> OperationResult[str, str]:
        if self._fail:
            return OperationResult.fail("écriture impossible (simulé)")
        self.exports.append((result, tuple(samples)))
        return OperationResult.ok(self.LOCATION)

    @property
    def last_samples(self) -> Optional[Tuple[AcquisitionThroughputSampleDTO, ...]]:
        return self.exports[-1][1] if self.exports else None
