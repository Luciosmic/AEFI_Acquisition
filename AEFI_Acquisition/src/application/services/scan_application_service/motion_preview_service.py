"""
Motion Preview Service - Application Layer

Responsibility:
- Generate trajectory previews with AtomicMotion information
- Calculate estimated durations
- Provide motion statistics for UI

Rationale:
- Allows users to preview scan trajectory before execution
- Shows estimated durations and motion profiles
- Helps users understand scan behavior
"""

from domain.models.scan.value_objects.step_scan_config import StepScanConfig
from domain.models.scan.scan_trajectory_factory import ScanTrajectoryFactory
from domain.models.scan.services.motion_profile_selector import MotionProfileSelector
from domain.models.scan.entities.atomic_motion import AtomicMotion
from application.dtos.motion_dtos import TrajectoryPreviewDTO, AtomicMotionDTO


class MotionPreviewService:
    """
    Service for generating motion previews from scan configuration.
    """
    
    def __init__(self, profile_selector: MotionProfileSelector = None):
        """
        Initialize with optional profile selector.
        
        Args:
            profile_selector: Custom selector (uses default if None)
        """
        self._profile_selector = profile_selector or MotionProfileSelector()
    
    def preview_trajectory(
        self,
        config: StepScanConfig
    ) -> TrajectoryPreviewDTO:
        """
        Generate a complete trajectory preview with motion information.
        
        Args:
            config: Scan configuration
            
        Returns:
            TrajectoryPreviewDTO with all motion details
        """
        # Generate trajectory
        trajectory = ScanTrajectoryFactory.create_trajectory(config)
        positions = list(trajectory.points)
        
        # Generate AtomicMotions
        motions = ScanTrajectoryFactory.create_motions(
            positions,
            self._profile_selector
        )
        
        # Convert to DTOs
        motion_dtos = []
        slow_count = 0
        fast_count = 0
        total_duration = 0.0
        
        for motion in motions:
            # Determine profile name
            profile_name = "slow" if motion.motion_profile == self._profile_selector.slow_profile else "fast"
            if profile_name == "slow":
                slow_count += 1
            else:
                fast_count += 1
            
            total_duration += motion.estimated_duration_seconds
            
            motion_dto = AtomicMotionDTO(
                id=str(motion.id),
                dx=motion.dx,
                dy=motion.dy,
                distance_mm=motion.get_distance(),
                estimated_duration_seconds=motion.estimated_duration_seconds,
                profile_name=profile_name,
                state="pending"
            )
            motion_dtos.append(motion_dto)
        
        return TrajectoryPreviewDTO(
            total_motions=len(motions),
            total_estimated_duration_seconds=total_duration,
            slow_motions_count=slow_count,
            fast_motions_count=fast_count,
            motions=motion_dtos
        )

