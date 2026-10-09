"""AefiCorrectedFieldMeasurement value object (see aefi_corrected_field_measurement_intention.md)."""

import math
from dataclasses import dataclass
from datetime import datetime

_FIELD_NAMES = (
    "field_x_in_phase", "field_x_quadrature",
    "field_y_in_phase", "field_y_quadrature",
    "field_z_in_phase", "field_z_quadrature",
)


@dataclass(frozen=True)
class AefiCorrectedFieldMeasurement:
    """A corrected AEFI measurement already transformed from the sensor frame to the
    source frame (TransformationService.transform_sensor_to_source). Distinct from
    AefiVoltageMeasurement: the grandeur is a field component, not a per-sensor-channel
    voltage."""

    # X direction
    field_x_in_phase: float  # Volts
    field_x_quadrature: float  # Volts

    # Y direction
    field_y_in_phase: float  # Volts
    field_y_quadrature: float  # Volts

    # Z direction
    field_z_in_phase: float  # Volts
    field_z_quadrature: float  # Volts

    # Metadata
    timestamp: datetime

    def __post_init__(self):
        """Validate field values are finite."""
        for field_name in _FIELD_NAMES:
            value = getattr(self, field_name)
            if not math.isfinite(value):
                raise ValueError(f"{field_name} must be finite, got {value}")
