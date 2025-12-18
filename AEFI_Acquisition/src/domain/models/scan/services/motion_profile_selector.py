"""
Motion Profile Selector - Domain Service

Responsibility:
- Select appropriate motion profile based on distance.
- Business logic: small distance = slow/precise, large distance = fast.
"""

from domain.models.test_bench.value_objects.motion_profile import MotionProfile


class MotionProfileSelector:
    """
    Domain service for selecting motion profiles based on distance.
    
    Selects appropriate profile:
    - Small distance (< threshold) → slow/precise profile
    - Large distance (>= threshold) → fast profile
    """
    
    def __init__(
        self,
        small_distance_threshold_mm: float = 5.0,
        slow_profile: MotionProfile = None,
        fast_profile: MotionProfile = None,
    ):
        """
        Initialize selector with thresholds and profiles.
        
        Args:
            small_distance_threshold_mm: Distance threshold for "small" vs "large" (default: 5mm)
            slow_profile: Profile for small distances (default: slow/precise)
            fast_profile: Profile for large distances (default: fast)
        """
        self.small_distance_threshold_mm = small_distance_threshold_mm
        
        # Default profiles if not provided
        if slow_profile is None:
            slow_profile = MotionProfile(
                min_speed=0.1,      # 0.1 mm/s
                target_speed=1.0,   # 1.0 mm/s
                acceleration=0.5,   # 0.5 mm/s²
                deceleration=0.5,   # 0.5 mm/s²
            )
        
        if fast_profile is None:
            fast_profile = MotionProfile(
                min_speed=0.5,      # 0.5 mm/s
                target_speed=10.0,  # 10.0 mm/s
                acceleration=5.0,   # 5.0 mm/s²
                deceleration=5.0,   # 5.0 mm/s²
            )
        
        self.slow_profile = slow_profile
        self.fast_profile = fast_profile
    
    def select_for_distance(self, distance_mm: float) -> MotionProfile:
        """
        Select motion profile based on distance.
        
        Args:
            distance_mm: Distance in millimeters
            
        Returns:
            Selected MotionProfile
        """
        if distance_mm < self.small_distance_threshold_mm:
            return self.slow_profile
        else:
            return self.fast_profile

