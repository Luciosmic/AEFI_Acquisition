"""
Motion DTO Mapper - Application Layer

Responsibility:
- Map AtomicMotion (domain) to AtomicMotionDTO (application)
- Map MotionProfile (domain) to MotionProfileDTO (application)

Rationale:
- Keeps mapping logic in application layer
- Provides clean separation between domain and presentation
"""

from domain.models.scan.entities.atomic_motion import AtomicMotion
from domain.models.test_bench.value_objects.motion_profile import MotionProfile
from domain.models.scan.value_objects.motion_state import MotionState
from application.dtos.motion_dtos import AtomicMotionDTO, MotionProfileDTO


class MotionDTOMapper:
    """
    Maps domain entities to DTOs for UI/API exposure.
    """
    
    @staticmethod
    def to_dto(atomic_motion: AtomicMotion, profile_name: str = "custom") -> AtomicMotionDTO:
        """
        Convert AtomicMotion to DTO.
        
        Args:
            atomic_motion: Domain AtomicMotion entity
            profile_name: Name of the profile ("slow", "fast", "custom")
            
        Returns:
            AtomicMotionDTO
        """
        return AtomicMotionDTO(
            id=str(atomic_motion.id),
            dx=atomic_motion.dx,
            dy=atomic_motion.dy,
            distance_mm=atomic_motion.get_distance(),
            estimated_duration_seconds=atomic_motion.estimated_duration_seconds,
            profile_name=profile_name,
            state=atomic_motion.execution_state.name.lower(),
            execution_motion_id=atomic_motion.execution_motion_id,
            actual_duration_seconds=None  # Will be filled when motion completes
        )
    
    @staticmethod
    def profile_to_dto(profile: MotionProfile, name: str = "custom") -> MotionProfileDTO:
        """
        Convert MotionProfile to DTO.
        
        Args:
            profile: Domain MotionProfile value object
            name: Profile name ("slow", "fast", "custom")
            
        Returns:
            MotionProfileDTO
        """
        return MotionProfileDTO(
            min_speed_mm_s=profile.min_speed,
            target_speed_mm_s=profile.target_speed,
            acceleration_mm_s2=profile.acceleration,
            deceleration_mm_s2=profile.deceleration,
            name=name
        )

