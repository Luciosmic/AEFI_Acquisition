from dataclasses import dataclass
from typing import List, NewType
from domain.shared.value_objects.position_2d import Position2D
from domain.shared.value_objects.vector_3d import Vector3D
from .electric_field_source import SphericalSource, SourceId

ColumnId = NewType('ColumnId', str)

@dataclass(frozen=True)
class Dimensions2D:
    width: float
    height: float

@dataclass(frozen=True)
class Column:
    """The movable carriage that carries the sources."""
    id: ColumnId
    dimensions: Dimensions2D
    position: Position2D
    sources: List[SphericalSource]

    def move_to(self, position: Position2D) -> None:
        # Placeholder logic (VOs should be immutable, so this might return a new Column or be a method on an Aggregate)
        pass

    def get_source_position(self, source_id: SourceId) -> Vector3D:
        # Placeholder
        return Vector3D(0.0, 0.0, 0.0)
