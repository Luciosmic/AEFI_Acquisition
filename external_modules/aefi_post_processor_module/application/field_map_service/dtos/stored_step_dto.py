from dataclasses import dataclass
from typing import Any, Dict

import numpy as np


@dataclass(frozen=True, eq=False)
class StoredStepDTO:
    """One stored processing step as the storage holds it: the array and the metadata, undecoded."""

    data: np.ndarray  # shape (N, N, channels)
    metadata: Dict[str, Any]
