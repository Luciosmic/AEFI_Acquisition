"""
Field Measurement Value Object

Responsibility:
- Immutable snapshot of an electric field reading, in V/m, for an arbitrary
  number of axes (mono/bi/tri-axial probes).
"""

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple


@dataclass(frozen=True)
class FieldMeasurement:
    """Electric field measurement in V/m — one value per probe axis."""

    components: Tuple[float, ...]
    timestamp: datetime
    uncertainty_estimate: Optional[float] = None
    std_dev_components: Optional[Tuple[float, ...]] = None

    def __post_init__(self):
        if not self.components:
            raise ValueError("components must have at least one value")
        for value in self.components:
            if not math.isfinite(value):
                raise ValueError(f"components must be finite, got {value}")
        if self.std_dev_components is not None:
            if len(self.std_dev_components) != len(self.components):
                raise ValueError(
                    f"std_dev_components length ({len(self.std_dev_components)}) "
                    f"must match components length ({len(self.components)})"
                )
            for value in self.std_dev_components:
                if not math.isfinite(value):
                    raise ValueError(f"std_dev_components must be finite, got {value}")

    @property
    def norm(self) -> float:
        return math.sqrt(sum(c**2 for c in self.components))
