from dataclasses import dataclass


@dataclass(frozen=True)
class SetRotationAnglesDTO:
    """Rotation angles (degrees) for the Sensor → Source coordinate transform."""
    theta_x: float
    theta_y: float
    theta_z: float
