from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple

import numpy as np


class IStepWriter(ABC):
    """
    Responsibility:
    - Store the computed steps of one acquisition with their metadata, and keep the history of what was stored.

    Rationale:
    - The service computes steps; where and how they are stored (an HDF5 group per step today) is not its concern.
    - Writing a step then reading it back must give the same values, whatever the storage.

    Design:
    - Outbound port, pure ABC, bound to one acquisition when built. Saving a step replaces the previous one of the same name.
    - load_step is the read-back that proves the write; an unknown step raises KeyError.
    """

    @abstractmethod
    def record_source(self, csv_path: str) -> None:
        """Remember which scan file the steps come from, and when it was read."""

    @abstractmethod
    def save_step(self, step_name: str, data: np.ndarray, metadata: Dict[str, Any]) -> None:
        """Store a step: its array and its metadata. Replaces a step of the same name."""

    @abstractmethod
    def load_step(self, step_name: str) -> Tuple[np.ndarray, Dict[str, Any]]:
        """The stored array and metadata of a step. KeyError if the step was never saved."""

    @abstractmethod
    def processing_history(self) -> List[str]:
        """The steps stored so far, in order, each with its timestamp."""

    @abstractmethod
    def close(self) -> None:
        """Release the storage."""
