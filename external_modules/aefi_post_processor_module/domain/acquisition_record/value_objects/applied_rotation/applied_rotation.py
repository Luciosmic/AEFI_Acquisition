"""
applied_rotation - The rotation of the sensor an acquisition applied, as its parameters file says it.
See applied_rotation_intention.md.
"""

import math
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class AppliedRotation:
    """
    The angles (theta_x, theta_y, theta_z) in degrees of the mounting rotation the acquisition used, with the
    convention they are expressed in, as three strings (type, order, direction): the post-processing reads them
    from the file and never reinterprets them.
    """

    angles: Tuple[float, float, float]
    convention_type: str
    convention_order: str
    convention_direction: str
    origin: Optional[str] = None  # "calibrated", "ideal_template"...: where the angles come from
    calibration_id: Optional[str] = None

    def __post_init__(self) -> None:
        if len(self.angles) != 3 or not all(math.isfinite(angle) for angle in self.angles):
            raise ValueError(f"An applied rotation needs three finite angles, got {self.angles!r}")
