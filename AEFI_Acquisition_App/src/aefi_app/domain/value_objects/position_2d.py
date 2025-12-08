from dataclasses import dataclass
import math

@dataclass(frozen=True)
class Position2D:
    x: float
    y: float

    def distance_to(self, other: 'Position2D') -> float:
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
