"""
Sensor Mounting Fit Value Object

See sensor_mounting_fit_intention.md.
"""

from dataclasses import dataclass

from domain.calibration.value_objects.sensor_rotation_angles.sensor_rotation_angles import SensorRotationAngles


@dataclass(frozen=True)
class SensorMountingFit:
    """Mounting angles fitted on the sensor responses, with the fit quality."""

    angles: SensorRotationAngles
    misalignment_x_degrees: float  # angle between P·r_X and +e_x^sources
    misalignment_y_degrees: float  # angle between P·r_Y and +e_y^sources
    response_separation_degrees: float  # angle between r_X and r_Y (ideally 90)
