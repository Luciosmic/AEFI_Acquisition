from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np


@dataclass(frozen=True, eq=False)
class ScanSamplesDTO:
    """What a scan file holds, as arrays: the position of each point and its channel values."""

    x: np.ndarray  # shape (n,)
    y: np.ndarray  # shape (n,)
    values: np.ndarray  # shape (n, number of channels)
    channel_names: Tuple[str, ...]
    sha256: Optional[str] = None  # SHA-256 of the file these points were read from; None when the reader does not hash
