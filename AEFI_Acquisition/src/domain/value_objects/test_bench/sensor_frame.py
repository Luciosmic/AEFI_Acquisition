from dataclasses import dataclass
from ..geometric.vector_3d import Vector3D
from ..geometric.frame_rotation import FrameRotation

@dataclass(frozen=True)
class SensorFrame:
    """
    Reference frame fixed to the center of the sensor.

    Notes:
    - Uses shared geometric VOs (Vector3D, FrameRotation).
    - Transformation methods are placeholders for now.
    """
    origin: Vector3D
    orientation: FrameRotation

    def to_global(self, local_pos: Vector3D) -> Vector3D:
        # Placeholder implementation
        return local_pos

    def to_local(self, global_pos: Vector3D) -> Vector3D:
        # Placeholder implementation
        return global_pos
