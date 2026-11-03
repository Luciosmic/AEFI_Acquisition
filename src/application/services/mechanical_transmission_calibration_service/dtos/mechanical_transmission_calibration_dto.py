from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class MechanicalTransmissionCalibrationDTO:
    """Current mechanical transmission — primitives only, no domain object
    crosses the application boundary. `driver_current_warning` is None when
    the driver delivers at least the motor's rated current."""

    motor_name: str
    stepper_driver_name: str
    microsteps: int
    driver_current_a: float
    driver_peak_current_a: float
    travel_per_motor_revolution_mm: float
    microns_per_pulse: float
    driver_current_warning: Optional[str]
    recorded_at: datetime
