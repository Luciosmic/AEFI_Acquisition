"""Sample value object (see sample_intention.md)."""

from dataclasses import dataclass

from domain.shared_kernel.value_objects.acquisition.aefi_voltage_measurement import AefiVoltageMeasurement


@dataclass(frozen=True)
class Sample:
    measurement: AefiVoltageMeasurement
