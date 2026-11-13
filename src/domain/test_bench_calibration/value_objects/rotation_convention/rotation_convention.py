"""
Rotation Convention Value Object

Responsibility:
- Name the convention in which sensor rotation angles are expressed, so a
  stored angle triplet is never ambiguous. Definition of the frames and of
  the mounting rotation P: rotation_convention_intention.md (reference).
"""

from dataclasses import dataclass

_SUPPORTED = ("extrinsic", "ZYX", "sources_to_sensor")


@dataclass(frozen=True)
class RotationConvention:
    """
    `type`/`order`: P = Rx(theta_x)·Ry(theta_y)·Rz(theta_z), rotations about
    the FIXED sources axes, applied Z then Y then X (scipy:
    `Rotation.from_euler('XYZ', [theta_x, theta_y, theta_z])`, uppercase).
    `direction`: P brings the sensor, aligned with the sources frame, to its
    current mounting — the columns of P are the sensor axes e_i^sensor
    expressed in the sources frame.
    Measurement: E_sensor = P^T·E_sources.
    Coordinate transform back to the sources frame: E_sources = P·E_sensor.

    Only this convention is supported — it is the one the application
    applies. Any other value is rejected instead of being silently
    applied the wrong way.
    """

    type: str
    order: str
    direction: str

    def __post_init__(self):
        if (self.type, self.order, self.direction) != _SUPPORTED:
            raise ValueError(
                f"Unsupported rotation convention (type={self.type!r}, order={self.order!r}, "
                f"direction={self.direction!r}); only {_SUPPORTED} is supported"
            )

    @staticmethod
    def standard() -> "RotationConvention":
        return RotationConvention(*_SUPPORTED)
