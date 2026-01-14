"""
WorkingVolume Value Object

Responsibility:
- Describe the 3D region of space over which the scanning head / sensor
  is expected to move during experiments.

Rationale:
- Encapsulate geometric limits of the bench in a single VO so that
  both bench configuration and scan planning can query it.
"""

from dataclasses import dataclass

from domain.value_objects.geometric.position_3d import Position3D


@dataclass(frozen=True)
class WorkingVolume:
    """
    Axis-aligned 3D box for the bench working volume.

    Coordinates are expressed in the bench global frame.
    """

    min_corner: Position3D
    max_corner: Position3D

    def contains(self, position: Position3D) -> bool:
        """Return True if `position` lies inside the volume (inclusive)."""
        return (
            self.min_corner.x <= position.x <= self.max_corner.x
            and self.min_corner.y <= position.y <= self.max_corner.y
            and self.min_corner.z <= position.z <= self.max_corner.z
        )


