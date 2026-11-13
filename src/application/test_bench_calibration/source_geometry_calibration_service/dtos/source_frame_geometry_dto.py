from dataclasses import dataclass
from typing import Tuple

Point2D = Tuple[float, float]
SpherePoints = Tuple[Point2D, Point2D, Point2D, Point2D]  # S1..S4


@dataclass(frozen=True)
class SourceFrameGeometryDTO:
    """Reconstructed sphere centers in the source frame (centroid origin, each
    sphere in its labeled quadrant) and their arrangement's deviation from a perfect
    square — primitives only. Distances follow the D_S1_S2, D_S3_S4, D_S1_S3,
    D_S1_S4, D_S2_S3, D_S2_S4 order."""

    sphere_positions_m: SpherePoints
    sphere_radii_m: Tuple[float, float, float, float]
    best_fit_square_positions_m: SpherePoints
    best_fit_square_side_m: float
    square_residuals_m: SpherePoints
    square_rms_residual_m: float
    distance_residuals_m: Tuple[float, float, float, float, float, float]
