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

from typing import List, Union
from domain.shared.value_objects.position_2d import Position2D
from domain.models.scan.value_objects.step_scan_config import StepScanConfig
from domain.models.scan.value_objects.fly_scan_config import FlyScanConfig
from domain.models.scan.value_objects.scan_pattern import ScanPattern
from domain.models.scan.value_objects.data_validation_result import DataValidationResult
from domain.models.scan.value_objects.scan_trajectory import ScanTrajectory
from domain.models.scan.entities.atomic_motion import AtomicMotion
from domain.models.scan.services.motion_profile_selector import MotionProfileSelector

class ScanTrajectoryFactory:
    """
    Factory for creating ScanTrajectory Value Objects.
    
    Encapsulates the logic for generating scan paths based on configuration.
    """
    
    @staticmethod
    def create_trajectory(config: Union[StepScanConfig, FlyScanConfig]) -> ScanTrajectory:
        """
        Create a ScanTrajectory for the given configuration.
        """
        positions = []
        zone = config.scan_zone
        
        # Calculate step sizes
        x_step = (zone.x_max - zone.x_min) / (config.x_nb_points - 1) if config.x_nb_points > 1 else 0
        y_step = (zone.y_max - zone.y_min) / (config.y_nb_points - 1) if config.y_nb_points > 1 else 0
        
        if config.scan_pattern == ScanPattern.SERPENTINE:
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
        
        elif config.scan_pattern == ScanPattern.RASTER:
            # Raster: always left to right
            for j in range(config.y_nb_points):
                y = zone.y_min + j * y_step
                for i in range(config.x_nb_points):
                    x = zone.x_min + i * x_step
                    positions.append(Position2D(x=x, y=y))
        
        elif config.scan_pattern == ScanPattern.COMB:
            # Comb: scan each column completely before moving to next
            for i in range(config.x_nb_points):
                x = zone.x_min + i * x_step
                for j in range(config.y_nb_points):
                    y = zone.y_min + j * y_step
                    positions.append(Position2D(x=x, y=y))
        
        return ScanTrajectory(points=positions)
    
    @staticmethod
    def create_motions(
        positions: List[Position2D],
        profile_selector: MotionProfileSelector
    ) -> List[AtomicMotion]:
        """
        Create AtomicMotions from a list of positions.
        
        Calculates relative displacements (dx, dy) between consecutive positions,
        selects appropriate motion profile based on distance, and creates AtomicMotion entities.
        
        Args:
            positions: List of absolute positions
            profile_selector: Service for selecting motion profiles
            
        Returns:
            List of AtomicMotion entities
        """
        if len(positions) < 2:
            return []  # Need at least 2 positions to create motions
        
        motions = []
        
        for i in range(len(positions) - 1):
            current = positions[i]
            next_pos = positions[i + 1]
            
            # Calculate relative displacement
            dx = next_pos.x - current.x
            dy = next_pos.y - current.y
            
            # Calculate distance
            distance = (dx ** 2 + dy ** 2) ** 0.5
            
            # Select profile based on distance
            profile = profile_selector.select_for_distance(distance)
            
            # Create AtomicMotion
            motion = AtomicMotion(
                dx=dx,
                dy=dy,
                motion_profile=profile
            )
            
            motions.append(motion)
        
        return motions
