from dataclasses import dataclass
from typing import NewType

from ..geometric.vector_3d import Vector3D  # Shared geometric VO
from .sensor_frame import SensorFrame

SensorId = NewType('SensorId', str)

@dataclass(frozen=True)
class Dimensions3D:
    width: float
    height: float
    depth: float

@dataclass(frozen=True)
class CubicSensor3D:
    """The physical sensor implementation."""
    id: SensorId
    dimensions: Dimensions3D
    frame: SensorFrame
    gain: float # from V to V/m
    bandwidth: float

    def get_measurement_point(self) -> Vector3D:
        # Placeholder
        return self.frame.origin

