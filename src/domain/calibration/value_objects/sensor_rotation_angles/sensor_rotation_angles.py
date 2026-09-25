"""
Sensor Rotation Angles Value Object

Responsibility:
- Carry the 3 angles of the mounting rotation P (brings the sensor from
  the sources frame to its current mounting; E_sensor = P^T·E_sources,
  E_sources = P·E_sensor), together with the convention they are
  expressed in. Definition of P and of the frames:
  rotation_convention/rotation_convention_intention.md.
"""

from dataclasses import dataclass, field

from domain.calibration.value_objects.rotation_convention.rotation_convention import RotationConvention


@dataclass(frozen=True)
class SensorRotationAngles:
    """
    Angles of the mounting rotation P (brings the sensor from the sources
    frame to its current mounting), in degrees.

    Unconstrained on purpose (mirrors SynchronousDetectionPhaseCalibrationPoint's
    delta_phi_degrees): any signed value is accepted, no wrapping.
    """

    theta_x_degrees: float
    theta_y_degrees: float
    theta_z_degrees: float
    convention: RotationConvention = field(default_factory=RotationConvention.standard)
