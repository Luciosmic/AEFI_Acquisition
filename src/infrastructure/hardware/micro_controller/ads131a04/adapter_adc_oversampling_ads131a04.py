"""
ADC Oversampling Adapter — ADS131A04 through the MCU

See adapter_adc_oversampling_ads131a04_intention.md.
"""

import logging
from typing import Tuple

from application.services.adc_output_rate_characterization_service.ports.i_adc_oversampling_port import (
    IAdcOversamplingPort,
)
from domain.shared_kernel.operation_result import OperationResult

logger = logging.getLogger(__name__)

# ADS131A04 datasheet, Table 30 — same list as ADS131Controller.
ALLOWED_OVERSAMPLING_RATIOS = (4096, 2048, 1024, 800, 768, 512, 400, 384, 256, 200, 192, 128, 96, 64, 48, 32)
CONFIGURATION_HARDWARE_ID = "ads131a04"  # ADS131A04AdvancedConfigurator.hardware_id


class AdapterAdcOversamplingAds131a04(IAdcOversamplingPort):
    """OSR written through ADS131Controller.set_oversampling_ratio (keeps the
    ICLK divider), never persisted to the configuration files."""

    def __init__(self, ads131_controller) -> None:
        self._controller = ads131_controller

    def get_oversampling_ratio(self) -> int:
        # ponytail: the controller's register shadow — the MCU protocol has no
        # register read-back. A power cycle of the ADC alone would desync it.
        return int(self._controller.memory_state["Oversampling_ratio"])

    def set_oversampling_ratio(self, oversampling_ratio: int) -> OperationResult[None, str]:
        if oversampling_ratio not in ALLOWED_OVERSAMPLING_RATIOS:
            return OperationResult.fail(f"OSR {oversampling_ratio} refusé par l'ADS131A04")
        ok, message = self._controller.set_oversampling_ratio(oversampling_ratio)
        if not ok:
            logger.warning("AdapterAdcOversamplingAds131a04: OSR %d not written: %s", oversampling_ratio, message)
            return OperationResult.fail(str(message))
        logger.info("AdapterAdcOversamplingAds131a04: OSR register set to %d (not persisted)", oversampling_ratio)
        return OperationResult.ok(None)

    def get_allowed_oversampling_ratios(self) -> Tuple[int, ...]:
        return ALLOWED_OVERSAMPLING_RATIOS

    def get_configuration_hardware_id(self) -> str:
        return CONFIGURATION_HARDWARE_ID
