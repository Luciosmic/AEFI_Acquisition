from dataclasses import dataclass
from ..vector_3d import Vector3D
from .spherical_source import SphericalSource
from .cubic_sensor import CubicSensor3D

@dataclass(frozen=True)
class SourceSensorAssociation:
    """Links a SphericalSource to a CubicSensor3D."""
    source: SphericalSource
    sensor: CubicSensor3D
    relative_position: Vector3D

    def is_valid(self) -> bool:
        return True
