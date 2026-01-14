"""
Arcus Motion Profile Adapter - Infrastructure

Responsibility:
- Adapt MotionProfile (domain) to Arcus hardware parameters
- Convert domain units (mm/s, mm/s²) to hardware units (Hz, steps/s²)

Rationale:
- Hardware-specific adaptation logic
- Keeps domain clean of hardware details
- Enables different adapters for different hardware
"""

from domain.models.test_bench.value_objects.motion_profile import MotionProfile
from infrastructure.hardware.arcus_performax_4EX.adapter_motion_port_arcus_performax4EX import ArcusAdapter


class ArcusMotionProfileAdapter:
    """
    Adapts MotionProfile to Arcus hardware parameters.
    
    Conversion:
    - Speed (mm/s) → Hz (steps/s)
    - Acceleration (mm/s²) → steps/s²
    """
    
    # Arcus conversion constants (from ArcusAdapter)
    MM_PER_STEP = 0.00436  # mm per step
    STEPS_PER_MM = 1.0 / MM_PER_STEP  # ~229.36 steps/mm
    
    @staticmethod
    def adapt_speed(profile: MotionProfile) -> int:
        """
        Convert target speed from mm/s to Hz (steps/s).
        
        Args:
            profile: MotionProfile with target_speed in mm/s
            
        Returns:
            Speed in Hz (steps/s) for Arcus hardware
        """
        speed_mm_s = profile.target_speed
        speed_hz = int(speed_mm_s * ArcusMotionProfileAdapter.STEPS_PER_MM)
        
        # Clamp to hardware limits (approx 10 to 100000 Hz)
        speed_hz = max(10, min(speed_hz, 100000))
        
        return speed_hz
    
    @staticmethod
    def apply_to_hardware(
        profile: MotionProfile,
        arcus_adapter: ArcusAdapter
    ) -> None:
        """
        Apply MotionProfile to Arcus hardware.
        
        Args:
            profile: MotionProfile to apply
            arcus_adapter: ArcusAdapter instance
        """
        # Convert and apply speed
        speed_hz = ArcusMotionProfileAdapter.adapt_speed(profile)
        
        # Note: ArcusAdapter.set_speed expects mm/s, but we could extend
        # to support direct Hz setting if needed
        speed_mm_s = profile.target_speed
        arcus_adapter.set_speed(speed_mm_s)
        
        # TODO: Apply acceleration/deceleration if Arcus supports it
        # For now, Arcus uses fixed acceleration curves

