from dataclasses import dataclass
from ..vector_3d import Vector3D
from .source import SphericalSource
from .sensor import CubicSensor3D

@dataclass(frozen=True)
class SourceSensorAssociation:
    """Links a SphericalSource to a CubicSensor3D."""
    source: SphericalSource
    sensor: CubicSensor3D
    relative_position: Vector3D

    def is_valid(self) -> bool:
        return True


from ..vector_3d import Vector3D
from ..frame_rotation import FrameRotation

@dataclass(frozen=True)
class SensorFrame:
    """Reference frame fixed to the center of the sensor."""
    origin: Vector3D  # Using Vector3D as Position3D for now if Position3D doesn't exist, or I should check if Position3D exists.
    orientation: FrameRotation

    def to_global(self, local_pos: Vector3D) -> Vector3D:
        # Placeholder implementation
        return local_pos

    def to_local(self, global_pos: Vector3D) -> Vector3D:
        # Placeholder implementation
        return global_pos
