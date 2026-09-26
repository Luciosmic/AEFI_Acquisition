from dataclasses import dataclass
from datetime import datetime
from typing import Tuple


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
