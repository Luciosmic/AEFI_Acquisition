"""
Caliper Measurement Value Object

Responsibility:
- Carry one caliper-measured value together with its GUM expanded
  uncertainty, reusable for any of the 10 raw source geometry readings
  (4 sphere diameters + 6 extremity-to-extremity distances).
"""

import math
from dataclasses import dataclass
from typing import ClassVar, Optional


@dataclass(frozen=True)
class CaliperMeasurement:
    """
    One caliper reading with its GUM (Guide to the Expression of
    Uncertainty in Measurement) expanded uncertainty.

    `uncertainty_expanded_m` is `U = k * u_c`, the same convention already
    hand-written in `aefi_device_config.json` (`uncertainty.expanded`, `k`).

    `uniform_half_width_m` is the half-width `a` of the uniform law the
    uncertainty was derived from (`u_c = a / sqrt(3)`), or None when the
    uncertainty was given directly.
    """

    # Half of the 0.02 mm vernier graduation: u_c = a/sqrt(3) = 0.02mm/(2*sqrt(3))
    DEFAULT_UNIFORM_HALF_WIDTH_M: ClassVar[float] = 0.00001

    value_m: float
    uncertainty_expanded_m: float
    k: float
    uniform_half_width_m: Optional[float] = None

    def __post_init__(self):
        if not math.isfinite(self.value_m) or self.value_m <= 0:
            raise ValueError(f"value_m must be finite and positive, got {self.value_m}")
        if not math.isfinite(self.uncertainty_expanded_m) or self.uncertainty_expanded_m < 0:
            raise ValueError(
                f"uncertainty_expanded_m must be finite and non-negative, got {self.uncertainty_expanded_m}"
            )
        if not math.isfinite(self.k) or self.k <= 0:
            raise ValueError(f"k must be finite and positive, got {self.k}")
        if self.uniform_half_width_m is not None:
            a = self.uniform_half_width_m
            if not math.isfinite(a) or a < 0:
                raise ValueError(f"uniform_half_width_m must be finite and non-negative, got {a}")
            if not math.isclose(self.uncertainty_expanded_m, self.k * a / math.sqrt(3), rel_tol=1e-9, abs_tol=1e-15):
                raise ValueError(
                    f"uncertainty_expanded_m={self.uncertainty_expanded_m} is not k*a/sqrt(3) "
                    f"for k={self.k}, uniform_half_width_m={a}"
                )

    @staticmethod
    def from_uniform_half_width(
        value_m: float, half_width_m: float = DEFAULT_UNIFORM_HALF_WIDTH_M, k: float = 2.0
    ) -> "CaliperMeasurement":
        """
        Build a measurement whose reading is known only to lie within
        `value_m ± half_width_m`, every value equally likely (uniform law):
        u_c = half_width_m / sqrt(3), expanded = k * u_c.

        The default half-width (0.01 mm, half the vernier graduation) gives
        the same standard uncertainty as `from_resolution`'s default.
        """
        return CaliperMeasurement(
            value_m=value_m,
            uncertainty_expanded_m=k * half_width_m / math.sqrt(3),
            k=k,
            uniform_half_width_m=half_width_m,
        )

    @staticmethod
    def from_uniform_expanded_uncertainty(
        value_m: float, uncertainty_expanded_m: float, k: float
    ) -> "CaliperMeasurement":
        """
        Rebuild a measurement whose expanded uncertainty is known to come
        from a uniform law, keeping that uncertainty as is and recovering
        its half-width: a = sqrt(3) * U / k. A reading recorded before the
        half-width was kept (vernier resolution 0.02 mm) comes back as 0.01 mm.
        """
        return CaliperMeasurement(
            value_m=value_m,
            uncertainty_expanded_m=uncertainty_expanded_m,
            k=k,
            uniform_half_width_m=math.sqrt(3) * uncertainty_expanded_m / k,
        )

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
        return CaliperMeasurement(
            value_m=value_m, uncertainty_expanded_m=k * u_c, k=k, uniform_half_width_m=resolution_m / 2
        )
