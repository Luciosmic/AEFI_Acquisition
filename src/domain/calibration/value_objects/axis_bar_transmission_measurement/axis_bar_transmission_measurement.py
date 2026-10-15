"""
Axis Bar Transmission Measurement Value Object

See axis_bar_transmission_measurement_intention.md.
"""

import math
from dataclasses import dataclass

from domain.calibration.value_objects.edge_bracket.edge_bracket import EdgeBracket

AXES = ("X", "Y")


@dataclass(frozen=True)
class AxisBarTransmissionMeasurement:
    """One axis measured with a bar of known length: N ± δ, then the
    travel per motor revolution ± its uncertainty."""

    axis: str
    bar_length_mm: float
    bar_length_uncertainty_mm: float
    first_front: EdgeBracket
    second_front: EdgeBracket
    full_steps_per_revolution: float
    microsteps: int

    def __post_init__(self):
        if self.axis not in AXES:
            raise ValueError(f"axis must be one of {AXES}, got {self.axis!r}")
        if not math.isfinite(self.bar_length_mm) or self.bar_length_mm <= 0:
            raise ValueError(f"bar_length_mm must be > 0, got {self.bar_length_mm}")
        if not math.isfinite(self.bar_length_uncertainty_mm) or self.bar_length_uncertainty_mm < 0:
            raise ValueError(f"bar_length_uncertainty_mm must be >= 0, got {self.bar_length_uncertainty_mm}")
        if self.full_steps_per_revolution <= 0:
            raise ValueError(f"full_steps_per_revolution must be > 0, got {self.full_steps_per_revolution}")
        if self.microsteps < 1:
            raise ValueError(f"microsteps must be >= 1, got {self.microsteps}")
        if self.increments_between_fronts <= self.increments_uncertainty:
            raise ValueError(
                f"fronts not separated: N={self.increments_between_fronts} <= "
                f"uncertainty {self.increments_uncertainty}"
            )

    @property
    def increments_between_fronts(self) -> float:
        """N = |n₂ − n₁|."""
        return abs(self.second_front.center_increment - self.first_front.center_increment)

    @property
    def increments_uncertainty(self) -> float:
        """δ₁ + δ₂."""
        return self.first_front.half_width_increments + self.second_front.half_width_increments

    @property
    def travel_per_motor_revolution_mm(self) -> float:
        """L · full_steps_per_revolution · microsteps / N."""
        return (
            self.bar_length_mm * self.full_steps_per_revolution * self.microsteps / self.increments_between_fronts
        )

    @property
    def relative_uncertainty(self) -> float:
        """ΔL / L + ΔN / N."""
        return (
            self.bar_length_uncertainty_mm / self.bar_length_mm
            + self.increments_uncertainty / self.increments_between_fronts
        )

    @property
    def travel_per_motor_revolution_uncertainty_mm(self) -> float:
        return self.travel_per_motor_revolution_mm * self.relative_uncertainty

    @property
    def microns_per_pulse(self) -> float:
        """The conversion this measurement would give (L / N, in µm)."""
        return 1000.0 * self.bar_length_mm / self.increments_between_fronts
