"""
Scan Trajectory Service - Domain Service

Responsibility:
- Generate scan trajectories (serpentine, raster, comb) based on configuration.
- Validate scan configuration.
- Pure business logic, no side effects, no I/O.

Rationale:
- Encapsulates the complex math/logic of path generation.
- Deterministic and easily testable.
"""

from typing import List
from ..value_objects.geometric.position_2d import Position2D
from ..value_objects.scan.step_scan_config import StepScanConfig
from ..value_objects.scan.scan_pattern import ScanPattern
from ..value_objects.scan.scan_axis import ScanAxis
from ..value_objects.validation_result import ValidationResult

from ..value_objects.scan.scan_trajectory import ScanTrajectory

class ScanTrajectoryFactory:
    """
    Factory for creating ScanTrajectory Value Objects.

    Encapsulates the logic for generating scan paths based on configuration.
    """

    @staticmethod
    def create_trajectory(config: StepScanConfig) -> ScanTrajectory:
        """Create a ScanTrajectory for the given configuration."""
        positions = []
        zone = config.scan_zone

        x_step = (zone.x_max - zone.x_min) / (config.x_nb_points - 1) if config.x_nb_points > 1 else 0
        y_step = (zone.y_max - zone.y_min) / (config.y_nb_points - 1) if config.y_nb_points > 1 else 0

        # axis=Y: outer loop on X, inner loop on Y (columns-first, preferred)
        # axis=X: outer loop on Y, inner loop on X (rows-first, legacy)
        y_first = config.scan_axis == ScanAxis.Y
        outer_count = config.x_nb_points if y_first else config.y_nb_points
        inner_count = config.y_nb_points if y_first else config.x_nb_points

        def make_pos(outer_idx: int, inner_idx: int) -> Position2D:
            if y_first:
                return Position2D(x=zone.x_min + outer_idx * x_step, y=zone.y_min + inner_idx * y_step)
            else:
                return Position2D(x=zone.x_min + inner_idx * x_step, y=zone.y_min + outer_idx * y_step)

        if config.scan_pattern == ScanPattern.SERPENTINE:
            for o in range(outer_count):
                inner_iter = range(inner_count) if o % 2 == 0 else range(inner_count - 1, -1, -1)
                for i in inner_iter:
                    positions.append(make_pos(o, i))

        elif config.scan_pattern == ScanPattern.RASTER:
            for o in range(outer_count):
                for i in range(inner_count):
                    positions.append(make_pos(o, i))

        elif config.scan_pattern == ScanPattern.COMB:
            # ponytail: COMB legacy behavior — Y-first columns, scan_axis ignored
            for col in range(config.x_nb_points):
                x = zone.x_min + col * x_step
                for row in range(config.y_nb_points):
                    y = zone.y_min + row * y_step
                    positions.append(Position2D(x=x, y=y))

        return ScanTrajectory(points=positions)
