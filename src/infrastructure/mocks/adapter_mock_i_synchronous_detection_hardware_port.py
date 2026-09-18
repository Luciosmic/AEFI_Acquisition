import logging
from typing import Dict, Optional

from application.services.synchronous_detection_service.ports.i_synchronous_detection_hardware_port import (
    ISynchronousDetectionHardwarePort,
)

logger = logging.getLogger(__name__)


class MockSynchronousDetectionHardwarePort(ISynchronousDetectionHardwarePort):
    """
    Mock implementation of the Synchronous Detection Hardware Port.

    Purely in-memory: mutates its own register dict on
    `set_ch3_phase_register`, no serial/SPI I/O.
    """

    def __init__(
        self,
        initial_registers: Optional[Dict[int, int]] = None,
        quadrature_enforced: bool = True,
        lock_in_gain: int = 10000,
        default_lock_in_gain: int = 10000,
    ) -> None:
        self.registers: Dict[int, int] = dict(
            initial_registers if initial_registers is not None else {1: 0, 2: 32768, 3: 16384, 4: 0}
        )
        self.quadrature_enforced = quadrature_enforced
        # Simulates ad9106_last_config.json's manually-persisted baseline —
        # set by tests to exercise restore_manual_configuration(); None means
        # "no manual baseline recorded yet" (a no-op restore).
        self.manual_baseline_registers: Optional[Dict[int, int]] = None
        self.restore_manual_configuration_calls = 0
        self.lock_in_gain = lock_in_gain
        self.default_lock_in_gain = default_lock_in_gain

    def get_all_channel_phase_registers(self) -> Dict[int, int]:
        return dict(self.registers)

    def set_ch3_phase_register(self, value: int, persist: bool = False) -> None:
        self.registers[3] = value
        logger.info("CH3 phase register set to %s (persist=%s)", value, persist)
        if persist:
            # Simulates ad9106_last_config.json being updated by a manual
            # edit — this becomes the new baseline restore_manual_configuration()
            # would reload.
            self.manual_baseline_registers = dict(self.registers)

    def restore_manual_configuration(self) -> None:
        self.restore_manual_configuration_calls += 1
        if self.manual_baseline_registers is not None:
            self.registers.update(self.manual_baseline_registers)
            logger.info("Manual baseline configuration restored")
        else:
            logger.info("restore_manual_configuration called with no baseline recorded — no-op")

    def is_quadrature_enforcement_enabled(self) -> bool:
        return self.quadrature_enforced

    def get_lock_in_gain(self) -> int:
        return self.lock_in_gain

    def get_default_lock_in_gain(self) -> int:
        return self.default_lock_in_gain

    def reset_lock_in_gain_to_default(self) -> None:
        self.lock_in_gain = self.default_lock_in_gain

    def zero_lock_in_gain(self) -> None:
        self.lock_in_gain = 0
