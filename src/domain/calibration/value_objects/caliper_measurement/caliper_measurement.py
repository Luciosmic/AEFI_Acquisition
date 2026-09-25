"""
Caliper Measurement Value Object

Responsibility:
- Carry one caliper-measured value together with its GUM expanded
  uncertainty, reusable for any of the 10 raw source geometry readings
  (4 sphere diameters + 6 extremity-to-extremity distances).
"""

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class CaliperMeasurement:
    """
    One caliper reading with its GUM (Guide to the Expression of
    Uncertainty in Measurement) expanded uncertainty.

    `uncertainty_expanded_m` is `U = k * u_c`, the same convention already
    hand-written in `aefi_device_config.json` (`uncertainty.expanded`, `k`).
    """

    value_m: float
    uncertainty_expanded_m: float
    k: float

    def __post_init__(self):
        if not math.isfinite(self.value_m) or self.value_m <= 0:
            raise ValueError(f"value_m must be finite and positive, got {self.value_m}")
        if not math.isfinite(self.uncertainty_expanded_m) or self.uncertainty_expanded_m < 0:
            raise ValueError(
                f"uncertainty_expanded_m must be finite and non-negative, got {self.uncertainty_expanded_m}"
            )
        if not math.isfinite(self.k) or self.k <= 0:
            raise ValueError(f"k must be finite and positive, got {self.k}")

    @staticmethod
    def from_resolution(value_m: float, resolution_m: float = 0.00002, k: float = 2.0) -> "CaliperMeasurement":
        """
        Build a measurement from a raw reading plus the instrument's
        resolution, computing the GUM expanded uncertainty for a single
        reading: u_c = resolution / (2*sqrt(3)) (rectangular distribution
        half-width / sqrt(3)), expanded = k * u_c.

        Defaults (0.02mm vernier resolution, k=2) match the values already
        hand-computed throughout `aefi_device_config.json`.
        """
        u_c = resolution_m / (2 * math.sqrt(3))
        return CaliperMeasurement(value_m=value_m, uncertainty_expanded_m=k * u_c, k=k)
