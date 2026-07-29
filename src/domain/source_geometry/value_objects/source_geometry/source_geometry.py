"""
Domain: Source Geometry

Responsibility:
    Raw, physically-measurable geometry of the 4 excitation spheres: the 6
    center-to-center pairwise distances (meters). This is what a caliper can
    actually measure on the bench — never coordinates in a global frame.

Rationale:
    See config_templates/NOTE - Source Frame Geometry.md §1-2. Coordinates
    only exist after running the DGP reconstruction (SourceFrameSolver).

Design:
    - Frozen dataclass (immutable)
    - Validates positivity only; degenerate-triangle / coplanarity checks
      belong to SourceFrameSolver, not to this raw-data holder.
"""
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class SourceGeometry:
    """Center-to-center pairwise distances (m) between the 4 excitation spheres.

    Naming mirrors config_templates/NOTE - Source Frame Geometry.md: d_ij is
    the distance between sphere Si and Sj.
    """

    d_12: float
    d_13: float
    d_14: float
    d_23: float
    d_24: float
    d_34: float

    def __post_init__(self):
        for name in ("d_12", "d_13", "d_14", "d_23", "d_24", "d_34"):
            value = getattr(self, name)
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite, got {value}")
            if value <= 0:
                raise ValueError(f"{name} must be positive, got {value}")
