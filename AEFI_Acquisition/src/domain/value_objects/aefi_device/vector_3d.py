from dataclasses import dataclass
import math

@dataclass(frozen=True)
class Vector3D:
    """
    Immutable representation of a 3D vector.
    """
    x: float
    y: float
    z: float

    def __add__(self, other: 'Vector3D') -> 'Vector3D':
        return Vector3D(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: 'Vector3D') -> 'Vector3D':
        return Vector3D(self.x - other.x, self.y - other.y, self.z - other.z)

    @property
    def magnitude(self) -> float:
        """Returns the Euclidean norm (length) of the vector."""
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

    def scale(self, scalar: float) -> 'Vector3D':
        """Multiply vector by a scalar."""
        return Vector3D(self.x * scalar, self.y * scalar, self.z * scalar)

    def normalize(self) -> 'Vector3D':
        """Returns a unit vector."""
        mag = self.magnitude
        if mag == 0:
            return Vector3D(0.0, 0.0, 0.0)
        return self.scale(1.0 / mag)
