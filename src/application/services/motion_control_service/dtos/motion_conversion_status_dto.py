from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class MotionConversionStatusDTO:
    """Whether the motion port has its mm/pulse conversion — primitives only.
    When not available: `motor_name` (None if no motor mounted), the
    `missing_quantity` and `where_to_enter` it."""

    is_available: bool
    microns_per_pulse: Optional[float] = None
    motor_name: Optional[str] = None
    missing_quantity: Optional[str] = None
    where_to_enter: Optional[str] = None
