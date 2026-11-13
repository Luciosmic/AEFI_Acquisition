from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class MechanicalTransmissionGapDTO:
    """What is missing to derive the mm/pulse conversion — primitives only.
    `motor_name` is None when no motor is mounted; `missing_quantity` is the
    operator-facing name of the missing quantity; `where_to_enter` says where
    it is entered."""

    motor_name: Optional[str]
    missing_quantity: str
    where_to_enter: str
