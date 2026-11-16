from dataclasses import dataclass
from typing import Tuple

import numpy as np


@dataclass(frozen=True, eq=False)
class ScanSamplesDTO:
    """What a scan file holds, as arrays: the position of each point and its channel values."""

    x: np.ndarray  # shape (n,)
    y: np.ndarray  # shape (n,)
    values: np.ndarray  # shape (n, number of channels)
    channel_names: Tuple[str, ...]
