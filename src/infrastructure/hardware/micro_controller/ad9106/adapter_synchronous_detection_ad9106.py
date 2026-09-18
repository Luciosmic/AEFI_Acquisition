"""
AD9106 Synchronous Detection Adapter - Infrastructure Layer

Responsibility:
- Implement ISynchronousDetectionHardwarePort interface
- Expose ch1-ch4 DDS phase registers (software-cached state) to the
  SynchronousDetectionService
- Write ch3's phase register via the single writer (AD9106AdvancedConfigurator.apply_config)
- Report the ch3/ch4 quadrature enforcement flag state (read-only)

Rationale:
- ch3/ch4 are the synchronous detection demodulation reference channels
  (ch1/ch2 remain the excitation port, see AdapterExcitationConfigurationAD9106).
- No new serial connection: reuses the AD9106Controller and
  AD9106AdvancedConfigurator instances already wired by MCUCompositionRoot.

Design:
- Hexagonal Architecture: thin Adapter — pure delegation, no logic of its own.
"""

import logging
from typing import Dict

from application.services.synchronous_detection_service.ports.i_synchronous_detection_hardware_port import (
    ISynchronousDetectionHardwarePort,
)
from infrastructure.hardware.micro_controller.ad9106.ad9106_controller import AD9106Controller
from infrastructure.hardware.micro_controller.ad9106.ad9106_advanced_configurator import AD9106AdvancedConfigurator

logger = logging.getLogger(__name__)


class AdapterSynchronousDetectionAD9106(ISynchronousDetectionHardwarePort):
    """
    Infrastructure adapter for AD9106 DDS synchronous detection hardware.
    Implements ISynchronousDetectionHardwarePort.
    """

    def __init__(self, controller: AD9106Controller, configurator: AD9106AdvancedConfigurator):
        """
        Args:
            controller: AD9106Controller instance (shared with the excitation adapter).
            configurator: AD9106AdvancedConfigurator instance (shared with the
                Hardware Advanced Config tab) — the single writer for all DDS registers.
        """
        self._controller = controller
        self._configurator = configurator

    def get_all_channel_phase_registers(self) -> Dict[int, int]:
        return dict(self._controller.get_memory_state()["DDS"]["Phase"])

    def set_ch3_phase_register(self, value: int) -> None:
        # persist=False: this is a transient, programmatic correction (the
        # synchronous-detection compensation), not the user's manually-tuned
        # baseline — must not overwrite ad9106_last_config.json (see
        # AD9106AdvancedConfigurator.apply_config's persist parameter).
        logger.debug("Setting ch3 phase register to %d (transient, not persisted)", value)
        self._configurator.apply_config({"ch3_phase": value}, persist=False)

    def restore_manual_configuration(self) -> None:
        logger.info("Restoring manual ch3/ch4 phase configuration")
        self._configurator.reload_last_config()

    def is_quadrature_enforcement_enabled(self) -> bool:
        return self._configurator.is_dds3_dds4_quadrature_enforced()

    def get_lock_in_gain(self) -> int:
        return self._controller.get_memory_state()["DDS"]["Gain"][3]

    def get_default_lock_in_gain(self) -> int:
        return self._configurator.get_default_ch3_gain()

    def reset_lock_in_gain_to_default(self) -> None:
        default_gain = self._configurator.get_default_ch3_gain()
        logger.info("Resetting lock-in gain (ch3/ch4) to default: %d", default_gain)
        self._configurator.apply_config({"ch3_gain": default_gain})
