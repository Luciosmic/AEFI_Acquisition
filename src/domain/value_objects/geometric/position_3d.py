from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Position3D:
    x: float
    y: float
    z: float

    def distance_to(self, other: "Position3D") -> float:
        return math.sqrt(
            (self.x - other.x) ** 2
            + (self.y - other.y) ** 2
            + (self.z - other.z) ** 2
        )


