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

import numpy as np
from scipy.spatial.transform import Rotation

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

    def mounting_matrix(self) -> np.ndarray:
        """P = Rx(θx)·Ry(θy)·Rz(θz): columns are the sensor axes in the sources frame."""
        x, y, z = np.radians([self.theta_x_degrees, self.theta_y_degrees, self.theta_z_degrees])
        rx = np.array([[1, 0, 0], [0, np.cos(x), -np.sin(x)], [0, np.sin(x), np.cos(x)]])
        ry = np.array([[np.cos(y), 0, np.sin(y)], [0, 1, 0], [-np.sin(y), 0, np.cos(y)]])
        rz = np.array([[np.cos(z), -np.sin(z), 0], [np.sin(z), np.cos(z), 0], [0, 0, 1]])
        return rx @ ry @ rz

    @classmethod
    def from_mounting_matrix(cls, matrix: np.ndarray) -> "SensorRotationAngles":
        """Inverse of mounting_matrix(): the angles whose P is `matrix` (a rotation).
        Uppercase 'XYZ' = Rx·Ry·Rz (see rotation_convention_intention.md)."""
        theta_x, theta_y, theta_z = Rotation.from_matrix(matrix).as_euler("XYZ", degrees=True)
        return cls(float(theta_x), float(theta_y), float(theta_z))
