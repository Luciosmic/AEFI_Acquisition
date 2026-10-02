"""
Mechanical Transmission Calibration Entry Entity

Responsibility:
- Immutable, append-only record of how the bench's motion chain is set up:
  motor and stepper driver mountings (by identity), driver settings and
  mechanical travel per motor revolution.
- Derive the distance per motor pulse, and flag a driver current below the
  motor's rating.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4


@dataclass(frozen=True)
class MechanicalTransmissionCalibrationEntry:
    """
    One registry entry: the motion chain as set up at a given time, shared
    by the X and Y axes.

    Entity — identity is `entry_id`. Immutable: a new setting is a new entry.
    """

    entry_id: UUID
    motor_mounting_id: UUID
    stepper_driver_mounting_id: UUID
    microsteps: int
    driver_current_a: float
    driver_peak_current_a: float
    travel_per_motor_revolution_mm: float
    recorded_at: datetime

    def __post_init__(self):
        if self.microsteps < 1:
            raise ValueError(f"microsteps must be >= 1, got {self.microsteps}")
        if self.driver_current_a <= 0:
            raise ValueError(f"driver_current_a must be > 0, got {self.driver_current_a}")
        if self.driver_peak_current_a < self.driver_current_a:
            raise ValueError(
                f"driver_peak_current_a ({self.driver_peak_current_a}) must be >= "
                f"driver_current_a ({self.driver_current_a})"
            )
        if self.travel_per_motor_revolution_mm <= 0:
            raise ValueError(
                f"travel_per_motor_revolution_mm must be > 0, got {self.travel_per_motor_revolution_mm}"
            )

    @staticmethod
    def single(
        motor_mounting_id: UUID,
        stepper_driver_mounting_id: UUID,
        microsteps: int,
        driver_current_a: float,
        driver_peak_current_a: float,
        travel_per_motor_revolution_mm: float,
    ) -> "MechanicalTransmissionCalibrationEntry":
        """Mint a fresh entry for a newly set up motion chain."""
        return MechanicalTransmissionCalibrationEntry(
            entry_id=uuid4(),
            motor_mounting_id=motor_mounting_id,
            stepper_driver_mounting_id=stepper_driver_mounting_id,
            microsteps=microsteps,
            driver_current_a=driver_current_a,
            driver_peak_current_a=driver_peak_current_a,
            travel_per_motor_revolution_mm=travel_per_motor_revolution_mm,
            recorded_at=datetime.now(timezone.utc),
        )

    def microns_per_pulse(self, full_steps_per_revolution: float) -> float:
        """Distance travelled per motor pulse, from the motor's steps per
        revolution (catalog) and this chain's microstepping and mechanics."""
        if full_steps_per_revolution <= 0:
            raise ValueError(f"full_steps_per_revolution must be > 0, got {full_steps_per_revolution}")
        return 1000.0 * self.travel_per_motor_revolution_mm / (full_steps_per_revolution * self.microsteps)

    def driver_current_shortfall(self, rated_current_a: float) -> Optional[str]:
        """Warning when the driver delivers less than the motor's rated
        current (lower torque, risk of skipped steps), else None."""
        if self.driver_current_a >= rated_current_a:
            return None
        return (
            f"Driver current {self.driver_current_a} A ({self.driver_peak_current_a} A peak) "
            f"below motor rated current {rated_current_a} A"
        )
