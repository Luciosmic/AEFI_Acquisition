"""
Fake ADC Output Rate Export Port

See fake_adc_output_rate_export_port_intention.md.
"""

from typing import List, Sequence, Tuple

from application.services.adc_output_rate_characterization_service.dtos.adc_output_rate_dtos import (
    AdcOutputRateCharacterizationDTO,
    DrdyCaptureDTO,
)
from application.services.adc_output_rate_characterization_service.ports.i_adc_output_rate_export_port import (
    IAdcOutputRateExportPort,
)
from domain.shared_kernel.operation_result import OperationResult


class FakeAdcOutputRateExportPort(IAdcOutputRateExportPort):
    LOCATION = "memory://adc_output_rate"

    def __init__(self, fail: bool = False) -> None:
        self._fail = fail
        self.exports: List[Tuple[AdcOutputRateCharacterizationDTO, Tuple[Tuple[int, DrdyCaptureDTO], ...]]] = []

    def export(
        self, result: AdcOutputRateCharacterizationDTO, captures: Sequence[Tuple[int, DrdyCaptureDTO]]
    ) -> OperationResult[str, str]:
        if self._fail:
            return OperationResult.fail("écriture impossible (simulé)")
        self.exports.append((result, tuple(captures)))
        return OperationResult.ok(self.LOCATION)
