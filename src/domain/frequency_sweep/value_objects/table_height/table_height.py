"""TableHeight value object (see table_height_intention.md)."""

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class TableHeight:
    """Height of the table under the sensor, in mm, as given by the operator."""

    millimetres: float

    def __post_init__(self):
        if not math.isfinite(self.millimetres):
            raise ValueError("table height must be a finite number of mm")
