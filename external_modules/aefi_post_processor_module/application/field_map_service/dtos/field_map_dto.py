from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np


@dataclass(frozen=True, eq=False)
class FieldMapDTO:
    """A stored step ready to draw: one 2D grid per channel and the extent [left, right, bottom, top]."""

    step_name: str
    grids: Dict[str, np.ndarray]
    extent: Tuple[float, float, float, float]
