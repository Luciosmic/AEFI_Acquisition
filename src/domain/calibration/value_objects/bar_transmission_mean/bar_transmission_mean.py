"""
Bar Transmission Mean Value Object

See bar_transmission_mean_intention.md.
"""

from dataclasses import dataclass

from domain.calibration.value_objects.axis_bar_transmission_measurement.axis_bar_transmission_measurement import (
    AxisBarTransmissionMeasurement,
)


@dataclass(frozen=True)
class BarTransmissionMean:
    """X and Y bar measurements combined into the common transmission, with their deviation."""

    x: AxisBarTransmissionMeasurement
    y: AxisBarTransmissionMeasurement

    def __post_init__(self):
        if self.x.axis != "X" or self.y.axis != "Y":
            raise ValueError(f"expected an X and a Y measurement, got {self.x.axis} and {self.y.axis}")
        if (
            self.x.full_steps_per_revolution != self.y.full_steps_per_revolution
            or self.x.microsteps != self.y.microsteps
        ):
            raise ValueError(
                "X and Y were measured with different motion chain settings "
                f"(steps/rev {self.x.full_steps_per_revolution} vs {self.y.full_steps_per_revolution}, "
                f"microsteps {self.x.microsteps} vs {self.y.microsteps})"
            )

    @property
    def travel_per_motor_revolution_mm(self) -> float:
        return (self.x.travel_per_motor_revolution_mm + self.y.travel_per_motor_revolution_mm) / 2.0

    @property
    def travel_per_motor_revolution_uncertainty_mm(self) -> float:
        return (
            self.x.travel_per_motor_revolution_uncertainty_mm + self.y.travel_per_motor_revolution_uncertainty_mm
        ) / 2.0

    @property
    def deviation_mm(self) -> float:
        """T_X − T_Y."""
        return self.x.travel_per_motor_revolution_mm - self.y.travel_per_motor_revolution_mm

    @property
    def relative_deviation(self) -> float:
        return self.deviation_mm / self.travel_per_motor_revolution_mm

    @property
    def axes_agree(self) -> bool:
        """|T_X − T_Y| within the sum of both uncertainties."""
        return abs(self.deviation_mm) <= (
            self.x.travel_per_motor_revolution_uncertainty_mm + self.y.travel_per_motor_revolution_uncertainty_mm
        )
