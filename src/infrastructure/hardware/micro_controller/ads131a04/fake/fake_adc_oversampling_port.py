"""
Fake ADC Oversampling Port

See fake_adc_oversampling_port_intention.md.
"""

from typing import List, Tuple

from application.services.adc_output_rate_characterization_service.ports.i_adc_oversampling_port import (
    IAdcOversamplingPort,
)
from domain.shared_kernel.operation_result import OperationResult

# ADS131A04 datasheet, Table 30 (same list as ADS131Controller).
ALLOWED_OVERSAMPLING_RATIOS = (4096, 2048, 1024, 800, 768, 512, 400, 384, 256, 200, 192, 128, 96, 64, 48, 32)


class FakeAdcOversamplingPort(IAdcOversamplingPort):
    """In-memory OSR register. `get_oversampling_ratio` can feed the fake DRDY
    capture so the simulated edges follow the OSR written here."""

    def __init__(self, oversampling_ratio: int = 4096, fail_on_set: bool = False) -> None:
        self._osr = oversampling_ratio
        self._fail_on_set = fail_on_set
        self.history: List[int] = []  # every OSR written, in order

    def get_oversampling_ratio(self) -> int:
        return self._osr

    def set_oversampling_ratio(self, oversampling_ratio: int) -> OperationResult[None, str]:
        # Same failure modes as the real adapter: value refused by the chip, write refused by the MCU.
        if oversampling_ratio not in ALLOWED_OVERSAMPLING_RATIOS:
            return OperationResult.fail(f"OSR {oversampling_ratio} refusé par l'ADS131A04")
        if self._fail_on_set:
            return OperationResult.fail("écriture du registre refusée par le MCU (simulé)")
        self._osr = oversampling_ratio
        self.history.append(oversampling_ratio)
        return OperationResult.ok(None)

    def get_allowed_oversampling_ratios(self) -> Tuple[int, ...]:
        return ALLOWED_OVERSAMPLING_RATIOS

    def get_configuration_hardware_id(self) -> str:
        return "ads131a04"  # same id as the real adapter
