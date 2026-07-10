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

    def __post_init__(self):
        if not self.components:
            raise ValueError("components must have at least one value")
        for value in self.components:
            if not math.isfinite(value):
                raise ValueError(f"components must be finite, got {value}")

    @property
    def norm(self) -> float:
        return math.sqrt(sum(c**2 for c in self.components))
