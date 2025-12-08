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
from ..value_objects.scan.scan_mode import ScanMode
from ..value_objects.validation_result import ValidationResult

from ..value_objects.scan.scan_trajectory import ScanTrajectory

class ScanTrajectoryFactory:
    """
    Factory for creating ScanTrajectory Value Objects.
    
    Encapsulates the logic for generating scan paths based on configuration.
    """
    
    @staticmethod
    def create_trajectory(config: StepScanConfig) -> ScanTrajectory:
        """
        Create a ScanTrajectory for the given configuration.
        """
        positions = []
        zone = config.scan_zone
        
        # Calculate step sizes
        x_step = (zone.x_max - zone.x_min) / (config.x_nb_points - 1) if config.x_nb_points > 1 else 0
        y_step = (zone.y_max - zone.y_min) / (config.y_nb_points - 1) if config.y_nb_points > 1 else 0
        
        if config.scan_mode == ScanMode.SERPENTINE:
            # Serpentine: alternating direction on each line
            for j in range(config.y_nb_points):
                y = zone.y_min + j * y_step
                if j % 2 == 0:
                    # Left to right
                    for i in range(config.x_nb_points):
                        x = zone.x_min + i * x_step
                        positions.append(Position2D(x=x, y=y))
                else:
                    # Right to left
                    for i in range(config.x_nb_points - 1, -1, -1):
                        x = zone.x_min + i * x_step
                        positions.append(Position2D(x=x, y=y))
        
        elif config.scan_mode == ScanMode.RASTER:
            # Raster: always left to right
            for j in range(config.y_nb_points):
                y = zone.y_min + j * y_step
                for i in range(config.x_nb_points):
                    x = zone.x_min + i * x_step
                    positions.append(Position2D(x=x, y=y))
        
        elif config.scan_mode == ScanMode.COMB:
            # Comb: scan each column completely before moving to next
            for i in range(config.x_nb_points):
                x = zone.x_min + i * x_step
                for j in range(config.y_nb_points):
                    y = zone.y_min + j * y_step
                    positions.append(Position2D(x=x, y=y))
        
        return ScanTrajectory(points=positions)
