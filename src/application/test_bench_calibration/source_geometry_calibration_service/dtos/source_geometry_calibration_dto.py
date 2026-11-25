from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple


@dataclass(frozen=True)
class SourceGeometryCalibrationDTO:
    """Latest recorded source geometry calibration — primitives only, no
    domain VO crosses the application -> interface boundary."""

    sphere_diameters_m: Tuple[float, float, float, float]
    sphere_diameters_uncertainty_m: Tuple[float, float, float, float]
    pairwise_distances_ext_m: Tuple[float, float, float, float, float, float]
    pairwise_distances_ext_uncertainty_m: Tuple[float, float, float, float, float, float]
    k: float
    recorded_at: datetime
    # Half-width of the uniform law behind the uncertainty, shared by every
    # diameter / every distance; None if the entry did not record one.
    diameter_half_width_m: Optional[float] = None
    distance_half_width_m: Optional[float] = None
