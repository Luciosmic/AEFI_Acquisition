"""
Fake Frequency Sweep Export Port

See fake_frequency_sweep_export_port_intention.md.
"""

from typing import List, Optional, Sequence, Tuple

from application.frequency_sweep.frequency_sweep_service.dtos.acquisition_parameters_dtos import (
    FrequencySweepAcquisitionParametersDTO,
)
from application.frequency_sweep.frequency_sweep_service.dtos.frequency_sweep_dtos import (
    FrequencySweepResultDTO,
    FrequencySweepSampleDTO,
)
from application.frequency_sweep.frequency_sweep_service.ports.i_frequency_sweep_export_port import IFrequencySweepExportPort
from application.shared.acquisition_parameters.acquisition_conditions_dtos import ExportedFileDTO
from domain.shared_kernel.operation_result import OperationResult


class FakeFrequencySweepExportPort(IFrequencySweepExportPort):
    """Keeps every export and every parameters write in memory; `fail=True`
    reproduces a location that cannot be created or written."""

    LOCATION = "memory://frequency_sweep"
    FILES = (
        ExportedFileDTO(name="frequency_response.csv", format="CSV", byte_size=100, sha256="0" * 64),
        ExportedFileDTO(name="samples.csv", format="CSV", byte_size=1000, sha256="1" * 64),
    )

    def __init__(self, fail: bool = False) -> None:
        self._fail = fail
        self.opened: List[Tuple[str, float]] = []
        self.exports: List[Tuple[FrequencySweepResultDTO, Tuple[FrequencySweepSampleDTO, ...]]] = []
        self.parameters_writes: List[FrequencySweepAcquisitionParametersDTO] = []

    def open_export(self, role: str, table_height_mm: float) -> OperationResult[str, str]:
        if self._fail:
            return OperationResult.fail("écriture impossible (simulé)")
        self.opened.append((role, table_height_mm))
        return OperationResult.ok(self.LOCATION)

    def export(
        self, location: str, result: FrequencySweepResultDTO, samples: Sequence[FrequencySweepSampleDTO]
    ) -> OperationResult[Tuple[ExportedFileDTO, ...], str]:
        if self._fail or location != self.LOCATION:
            return OperationResult.fail("écriture impossible (simulé)")
        self.exports.append((result, tuple(samples)))
        return OperationResult.ok(self.FILES)

    def write_acquisition_parameters(
        self, location: str, parameters: FrequencySweepAcquisitionParametersDTO
    ) -> OperationResult[None, str]:
        if self._fail or location != self.LOCATION:
            return OperationResult.fail("écriture impossible (simulé)")
        self.parameters_writes.append(parameters)
        return OperationResult.ok(None)

    @property
    def last_samples(self) -> Optional[Tuple[FrequencySweepSampleDTO, ...]]:
        return self.exports[-1][1] if self.exports else None

    @property
    def last_parameters(self) -> Optional[FrequencySweepAcquisitionParametersDTO]:
        return self.parameters_writes[-1] if self.parameters_writes else None
