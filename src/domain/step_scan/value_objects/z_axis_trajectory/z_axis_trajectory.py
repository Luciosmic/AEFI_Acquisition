"""
Z Axis Trajectory Value Object

Responsibility:
- Ordered heights to visit at a fixed XY position (Z-scan "Consignes").
- Same ergonomics as ScanTrajectory; iteration yields z values (mm).
"""

from dataclasses import dataclass
from typing import Iterator, List
from domain.shared_kernel.value_objects.geometric.position_2d import Position2D


@dataclass(frozen=True)
class ZAxisTrajectory:
    xy_position: Position2D
    z_values: List[float]

    def __iter__(self) -> Iterator[float]:
        return iter(self.z_values)

    def __len__(self) -> int:
        return len(self.z_values)

    def __getitem__(self, index) -> float:
        return self.z_values[index]

    @property
    def total_points(self) -> int:
        return len(self.z_values)
