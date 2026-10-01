"""
Hardware Signature Value Object

Responsibility:
- Identify the hardware setup a calibration entry was recorded on, by
  reference: the identities of the mounted boards and of the sensor.
"""

from dataclasses import dataclass

from domain.calibration.value_objects.hardware_component_name.hardware_component_name import (
    HardwareComponentName,
)


@dataclass(frozen=True)
class HardwareSignature:
    """
    Immutable reference to the hardware setup a calibration applies to.

    All three fields are identities (`HardwareComponentName`) of components
    in the hardware component catalog — the mounted boards and sensor —
    references, not copies of their characterization.
    """

    excitation_electronics_board_name: HardwareComponentName
    conditioning_electronics_board_name: HardwareComponentName
    sensor_name: HardwareComponentName

    def __post_init__(self):
        if not self.excitation_electronics_board_name:
            raise ValueError("excitation_electronics_board_name must not be empty")
        if not self.conditioning_electronics_board_name:
            raise ValueError("conditioning_electronics_board_name must not be empty")
        if not self.sensor_name:
            raise ValueError("sensor_name must not be empty")
