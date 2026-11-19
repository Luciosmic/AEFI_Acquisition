from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class AppliedRotationDTO:
    """The rotation of the sensor an acquisition applied: angles in degrees (theta_x, theta_y, theta_z) and their convention."""

    angles: Tuple[float, float, float]
    convention_type: str
    convention_order: str
    convention_direction: str
    origin: Optional[str] = None
    calibration_id: Optional[str] = None
