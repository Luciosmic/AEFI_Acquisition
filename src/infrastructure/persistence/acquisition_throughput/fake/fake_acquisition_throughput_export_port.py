"""
Fake Acquisition Throughput Export Port

See fake_acquisition_throughput_export_port_intention.md.
"""

from typing import List, Optional, Sequence, Tuple

from application.shared.acquisition_parameters.acquisition_conditions_dtos import (
    ExportedFileDTO,
)
from application.services.acquisition_throughput_characterization_service.dtos.acquisition_parameters_dtos import (
    AcquisitionParametersDTO,
)
from application.services.acquisition_throughput_characterization_service.dtos.acquisition_throughput_dtos import (
    AcquisitionThroughputCharacterizationDTO,
    AcquisitionThroughputSampleDTO,
)
from application.services.acquisition_throughput_characterization_service.ports.i_acquisition_throughput_export_port import (
    IAcquisitionThroughputExportPort,
)
from domain.shared_kernel.operation_result import OperationResult


class FakeAcquisitionThroughputExportPort(IAcquisitionThroughputExportPort):
    """Keeps every export and every parameters write in memory; `fail=True`
    reproduces a location that cannot be created or written."""

    LOCATION = "memory://acquisition_throughput"
    FILES = (
        ExportedFileDTO(name="summary.csv", format="CSV", byte_size=100, sha256="0" * 64),
        ExportedFileDTO(name="samples.csv", format="CSV", byte_size=1000, sha256="1" * 64),
    )

    def __init__(self, fail: bool = False) -> None:
        self._fail = fail
        self.opened: List[Tuple[int, str]] = []
        self.exports: List[Tuple[AcquisitionThroughputCharacterizationDTO, Tuple[AcquisitionThroughputSampleDTO, ...]]] = []
        self.parameters_writes: List[AcquisitionParametersDTO] = []

    def open_export(self, oversampling_ratio: int, excitation_label: str) -> OperationResult[str, str]:
        if self._fail:
            return OperationResult.fail("écriture impossible (simulé)")
        self.opened.append((oversampling_ratio, excitation_label))
        return OperationResult.ok(self.LOCATION)

    def export(
        self,
        location: str,
        result: AcquisitionThroughputCharacterizationDTO,
        samples: Sequence[AcquisitionThroughputSampleDTO],
    ) -> OperationResult[Tuple[ExportedFileDTO, ...], str]:
        if self._fail or location != self.LOCATION:
            return OperationResult.fail("écriture impossible (simulé)")
        self.exports.append((result, tuple(samples)))
        return OperationResult.ok(self.FILES)

    def write_acquisition_parameters(
        self, location: str, parameters: AcquisitionParametersDTO
    ) -> OperationResult[None, str]:
        if self._fail or location != self.LOCATION:
            return OperationResult.fail("écriture impossible (simulé)")
        self.parameters_writes.append(parameters)
        return OperationResult.ok(None)

    @property
    def last_samples(self) -> Optional[Tuple[AcquisitionThroughputSampleDTO, ...]]:
        return self.exports[-1][1] if self.exports else None

    @property
    def last_parameters(self) -> Optional[AcquisitionParametersDTO]:
        return self.parameters_writes[-1] if self.parameters_writes else None
