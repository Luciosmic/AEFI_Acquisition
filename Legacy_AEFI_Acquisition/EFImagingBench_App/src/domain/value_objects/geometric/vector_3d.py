from dataclasses import dataclass
import math

@dataclass(frozen=True)
class Vector3D:
    x: float
    y: float
    z: float

    def magnitude(self) -> float:
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)
