"""
MCU Acquisition Averaging Adapter

See adapter_acquisition_averaging_mcu_intention.md.
"""

import logging
from typing import Tuple

from application.services.acquisition_throughput_characterization_service.ports.i_acquisition_averaging_port import (
    IAcquisitionAveragingPort,
)
from domain.shared_kernel.operation_result import OperationResult
from infrastructure.hardware.micro_controller.mcu_advanced_configurator import MCUAdvancedConfigurator

logger = logging.getLogger(__name__)

ADC_CONFIGURATION_HARDWARE_ID = "ads131a04"  # ADS131A04AdvancedConfigurator.hardware_id


class AdapterAcquisitionAveragingMcu(IAcquisitionAveragingPort):
    """n_avg through MCUAdvancedConfigurator (same writer as the Hardware
    Config tab); OSR from the ADS131A04 controller's register shadow."""

    def __init__(self, mcu_configurator: MCUAdvancedConfigurator, ads131_controller) -> None:
        self._mcu_configurator = mcu_configurator
        self._ads131_controller = ads131_controller

    def get_n_avg(self) -> int:
        return self._mcu_configurator.get_n_avg()

    def set_n_avg(self, n_avg: int) -> OperationResult[None, str]:
        try:
            self._mcu_configurator.apply_config({"n_avg": n_avg})
        except (ValueError, OSError) as error:
            logger.warning("AdapterAcquisitionAveragingMcu: n_avg=%s not applied: %s", n_avg, error)
            return OperationResult.fail(str(error))
        return OperationResult.ok(None)

    def get_n_avg_range(self) -> Tuple[int, int]:
        return MCUAdvancedConfigurator.NAVG_MIN, MCUAdvancedConfigurator.NAVG_MAX

    def get_oversampling_ratio(self) -> int:
        return int(self._ads131_controller.memory_state["Oversampling_ratio"])

    def get_configuration_hardware_ids(self) -> Tuple[str, ...]:
        # n_avg: the MCU configurator; OSR: ADS131A04AdvancedConfigurator ("ads131a04").
        return self._mcu_configurator.hardware_id, ADC_CONFIGURATION_HARDWARE_ID
