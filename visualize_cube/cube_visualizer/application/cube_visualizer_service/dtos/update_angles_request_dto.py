from dataclasses import dataclass


@dataclass(frozen=True)
class UpdateAnglesRequestDto:
    """Request DTO for updating the sensor orientation angles."""
    theta_x: float
    theta_y: float
    theta_z: float
