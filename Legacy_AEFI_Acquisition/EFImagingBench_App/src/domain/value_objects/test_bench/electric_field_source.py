from dataclasses import dataclass
from enum import Enum, auto
from typing import NewType
from ..vector_3d import Vector3D

SourceId = NewType('SourceId', str)

class Quadrant(Enum):
    X_POS = auto()
    Y_POS = auto()
    X_NEG = auto()
    Y_NEG = auto()

@dataclass(frozen=True)
class SphericalSource:
    """One of the four excitation sources mounted on the column."""
    id: SourceId
    quadrant: Quadrant
    position_on_column: Vector3D

    def get_excitation_field(self, target: Vector3D) -> Vector3D:
        # Placeholder
        return Vector3D(0.0, 0.0, 0.0)
