"""
Hardware Signature Value Object

Responsibility:
- Identify the hardware setup (board revisions, sensor) a calibration
  entry was recorded on.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class HardwareSignature:
    """
    Immutable identifier of the hardware setup a calibration applies to.

    Read from `config_templates/aefi_device_config.json` by
    `HardwareSignatureReader` (infrastructure) — this VO itself has no
    knowledge of that file.
    """

    excitation_board_version: str
    conditioning_board_version: str
    sensor_version: str
    sensor_serial_number: Optional[str]

    def __post_init__(self):
        if not self.excitation_board_version:
            raise ValueError("excitation_board_version must not be empty")
        if not self.conditioning_board_version:
            raise ValueError("conditioning_board_version must not be empty")
        if not self.sensor_version:
            raise ValueError("sensor_version must not be empty")
