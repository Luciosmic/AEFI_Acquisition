"""
ScanningHead Entity

Responsibility:
- Represent the movable head (or carriage) that carries the sensor/device
  over the test bench working volume.

Rationale:
- Explicit entity to separate the *bench configuration* (TestBench aggregate)
  from the *current pose* of the moving part.
"""

from dataclasses import dataclass

from domain.value_objects.geometric.position_2d import Position2D


@dataclass
class ScanningHead:
    """
    Entity representing the current 2D position of the scanning head.

    Notes:
    - Z coordinate, tilt, etc. can be added later if needed.
    """

    position: Position2D

    def move_to(self, target: Position2D) -> None:
        """
        Update the head position in the domain model.

        Application services are responsible for coordinating this with
        actual hardware motion.
        """
        self.position = target


