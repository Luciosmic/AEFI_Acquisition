"""
Source Geometry

Responsibility:
    Raw, physically-measurable geometry of the 4 excitation spheres. Sphere
    centers are not accessible to a caliper, so what's actually measured is
    the extremity-to-extremity distance between spheres (D_ij) and each
    sphere's diameter (phi_i) individually. Center-to-center distances
    (needed by the DGP reconstruction) are derived, not stored.

Rationale:
    See "NOTE - Source Frame Geometry" (Luis Saluden's vault, not tracked in
    this repo) sections 1-2. The config only ever encodes what was actually
    measured with a caliper.

Design:
    - Frozen dataclass (immutable) over the 6 raw D_ij + 4 raw phi_i.
    - r_i = phi_i / 2 and d_ij = D_ij - r_i - r_j exposed as read-only
      properties, computed on demand rather than stored.
    - Validates positivity/finiteness of every raw reading, and that each
      derived center-to-center distance stays positive (spheres measured as
      overlapping would mean a measurement error, not a valid geometry).
"""
import math
from dataclasses import dataclass

_RAW_FIELDS = (
    "D_12", "D_13", "D_14", "D_23", "D_24", "D_34",
    "phi_1", "phi_2", "phi_3", "phi_4",
)


@dataclass(frozen=True)
class SourceGeometry:
    """Extremity-to-extremity distances (m) and per-sphere diameters (m),
    as read directly off the caliper.

    Naming mirrors "NOTE - Source Frame Geometry": D_ij is the measured span
    between the outer extremities of Si and Sj; phi_i is the diameter of Si.
    """

    D_12: float
    D_13: float
    D_14: float
    D_23: float
    D_24: float
    D_34: float
    phi_1: float
    phi_2: float
    phi_3: float
    phi_4: float

    def __post_init__(self):
        for name in _RAW_FIELDS:
            value = getattr(self, name)
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite, got {value}")
            if value <= 0:
                raise ValueError(f"{name} must be positive, got {value}")

        for name, value in (
            ("d_12", self.d_12), ("d_13", self.d_13), ("d_14", self.d_14),
            ("d_23", self.d_23), ("d_24", self.d_24), ("d_34", self.d_34),
        ):
            if value <= 0:
                raise ValueError(
                    f"Derived center-to-center {name} is not positive ({value:.3e} m): "
                    "spheres would overlap given the measured diameters"
                )

    @property
    def r_1(self) -> float:
        return self.phi_1 / 2

    @property
    def r_2(self) -> float:
        return self.phi_2 / 2

    @property
    def r_3(self) -> float:
        return self.phi_3 / 2

    @property
    def r_4(self) -> float:
        return self.phi_4 / 2

    @property
    def d_12(self) -> float:
        return self.D_12 - self.r_1 - self.r_2

    @property
    def d_13(self) -> float:
        return self.D_13 - self.r_1 - self.r_3

    @property
    def d_14(self) -> float:
        return self.D_14 - self.r_1 - self.r_4

    @property
    def d_23(self) -> float:
        return self.D_23 - self.r_2 - self.r_3

    @property
    def d_24(self) -> float:
        return self.D_24 - self.r_2 - self.r_4

    @property
    def d_34(self) -> float:
        return self.D_34 - self.r_3 - self.r_4
