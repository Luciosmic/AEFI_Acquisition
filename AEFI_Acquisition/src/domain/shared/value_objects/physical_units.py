"""
Shared physical units.

Responsibility:
- Provide simple, explicit value objects for physical quantities
  (e.g. Voltage) to avoid mixing plain floats and units.

Notes:
- These classes are not yet widely used; they are introduced as a
  foundation for future refactors. Existing `VoltageMeasurement`
  continues to be the main carrier for acquisition data.
"""

from dataclasses import dataclass
from typing import Literal


UnitVoltage = Literal["V"]


@dataclass(frozen=True)
class Voltage:
    """Scalar voltage with explicit unit (volts)."""

    value: float
    unit: UnitVoltage = "V"

    def __post_init__(self) -> None:
        # Simple sanity check; more constraints can be added later.
        if self.unit != "V":
            raise ValueError(f"Unsupported voltage unit: {self.unit}")


__all__ = ["Voltage", "UnitVoltage"]



