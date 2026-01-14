"""
Motion Adapter Service - Infrastructure

Responsibility:
- Adapt AtomicMotion (domain) to hardware commands (infrastructure)
- Apply MotionProfile to hardware before execution
- Convert relative motion (dx, dy) to absolute positions

Rationale:
- Decouples domain (AtomicMotion) from infrastructure (IMotionPort)
- Enables profile application to hardware
- Makes AtomicMotion a first-class concept in execution
"""

from domain.models.scan.entities.atomic_motion import AtomicMotion
from domain.shared.value_objects.position_2d import Position2D
from application.services.motion_control_service.i_motion_port import IMotionPort
from domain.models.test_bench.value_objects.motion_profile import MotionProfile


class MotionAdapterService:
    """
    Adapts AtomicMotion entities to hardware motion commands.
    
    This service bridges the gap between domain concepts (AtomicMotion)
    and infrastructure commands (IMotionPort.move_to).
    """
    
    def __init__(self, motion_port: IMotionPort):
        """
        Initialize the adapter with a motion port.
        
        Args:
            motion_port: The hardware motion port to use
        """
        self._motion_port = motion_port
    
    def execute_atomic_motion(
        self,
        motion: AtomicMotion,
        current_position: Position2D
    ) -> str:
        """
        Execute an AtomicMotion via the motion port.
        
        Steps:
        1. Calculate target position (current + dx/dy)
        2. Apply MotionProfile to hardware (if supported)
        3. Execute move_to
        4. Return motion_id for event tracking
        
        Args:
            motion: The AtomicMotion to execute
            current_position: Current position before motion
            
        Returns:
            motion_id: Execution motion ID for event tracking
        """
        # 1. Calculate target position
        target_position = Position2D(
            x=current_position.x + motion.dx,
            y=current_position.y + motion.dy
        )
        
        # Log AtomicMotion information
        distance_mm = motion.get_distance()
        print(f"[AtomicMotion] Executing motion ID={str(motion.id)[:8]}... | "
              f"dx={motion.dx:.2f}mm, dy={motion.dy:.2f}mm, distance={distance_mm:.2f}mm | "
              f"from ({current_position.x:.1f}, {current_position.y:.1f}) → ({target_position.x:.1f}, {target_position.y:.1f})")
        print(f"[AtomicMotion] MotionProfile: min_speed={motion.motion_profile.min_speed:.2f}mm/s, "
              f"target_speed={motion.motion_profile.target_speed:.2f}mm/s, "
              f"accel={motion.motion_profile.acceleration:.2f}mm/s², "
              f"decel={motion.motion_profile.deceleration:.2f}mm/s² | "
              f"estimated_duration={motion.estimated_duration_seconds*1000:.1f}ms")
        
        # 2. Apply motion profile to hardware
        # Note: This is a placeholder - actual implementation depends on hardware capabilities
        self._apply_motion_profile(motion.motion_profile)
        
        # 2.5. Set motion profile in mock (if it's a MockMotionPort)
        # This allows the mock to use domain-calculated duration for realistic simulation
        if hasattr(self._motion_port, 'set_motion_profile'):
            self._motion_port.set_motion_profile(
                motion.motion_profile,
                motion.estimated_duration_seconds
            )
        
        # 3. Execute movement
        motion_id = self._motion_port.move_to(target_position)
        
        # 4. Return motion_id for tracking
        return motion_id
    
    def _apply_motion_profile(self, profile: MotionProfile) -> None:
        """
        Apply motion profile to hardware.
        
        For now, we apply the target speed. Full profile application
        (acceleration/deceleration) depends on hardware capabilities.
        
        Args:
            profile: MotionProfile to apply
        """
        # Convert mm/s to cm/s (if motion_port.set_speed expects cm/s)
        # Or adapt based on hardware requirements
        speed_cm_s = profile.target_speed / 10.0  # mm/s → cm/s
        
        try:
            self._motion_port.set_speed(speed_cm_s)
        except (AttributeError, NotImplementedError):
            # Hardware doesn't support speed setting, skip
            pass

