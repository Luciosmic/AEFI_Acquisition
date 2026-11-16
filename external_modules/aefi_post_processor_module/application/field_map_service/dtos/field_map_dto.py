from dataclasses import dataclass, field
from typing import Any, Dict, Tuple

import numpy as np


@dataclass(frozen=True, eq=False)
class FieldMapDTO:
    """A stored step ready to draw: one 2D grid per channel, the extent [left, right, bottom, top] and the metadata stored with it."""

    step_name: str
    grids: Dict[str, np.ndarray]
    extent: Tuple[float, float, float, float]
    metadata: Dict[str, Any] = field(default_factory=dict)  # as stored: rotation angles and reference point among others
