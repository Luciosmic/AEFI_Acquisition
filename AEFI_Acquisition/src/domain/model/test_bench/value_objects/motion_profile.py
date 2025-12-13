from dataclasses import dataclass

@dataclass(frozen=True)
class MotionProfile:
    """
    Defines the kinematic parameters for motion.
    
    Attributes:
        min_speed: Minimum/Start speed (mm/s).
        target_speed: Target/Cruising speed (mm/s).
        acceleration: Acceleration rate (mm/s²).
        deceleration: Deceleration rate (mm/s²).
    """
    min_speed: float
    target_speed: float
    acceleration: float
    deceleration: float

    def __post_init__(self):
        if self.min_speed < 0 or self.target_speed < 0:
            raise ValueError("Speeds must be non-negative.")
        if self.acceleration <= 0 or self.deceleration <= 0:
            raise ValueError("Acceleration and deceleration must be positive.")
        if self.min_speed > self.target_speed:
            raise ValueError("Minimum speed cannot be greater than target speed.")
