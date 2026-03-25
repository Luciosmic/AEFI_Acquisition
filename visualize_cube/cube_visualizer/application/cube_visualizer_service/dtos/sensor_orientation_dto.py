from dataclasses import dataclass


@dataclass(frozen=True)
class SensorOrientationDto:
    """Response DTO representing a sensor orientation as Euler angles."""
    theta_x: float
    theta_y: float
    theta_z: float
