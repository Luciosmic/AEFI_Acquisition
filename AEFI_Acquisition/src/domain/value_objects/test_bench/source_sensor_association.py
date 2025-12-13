from dataclasses import dataclass

from ..geometric.vector_3d import Vector3D          # Shared geometric VO
from ..geometric.frame_rotation import FrameRotation  # Shared geometric VO
from .electric_field_source import SphericalSource
from .electric_field_sensor import CubicSensor3D


@dataclass(frozen=True)
class SourceSensorAssociation:
    """
    Links a SphericalSource to a CubicSensor3D in the bench geometry.

    Responsibility:
    - Capture which source is paired with which sensor and with what
      relative position vector.
    """
    source: SphericalSource
    sensor: CubicSensor3D
    relative_position: Vector3D

    def is_valid(self) -> bool:
        # Placeholder for future geometric consistency checks.
        return True


