from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple

import numpy as np

from ..dtos.scan_samples_dto import ScanSamplesDTO
from ..dtos.source_record_dto import SourceRecordDTO


class IStepWriter(ABC):
    """
    Responsibility:
    - Store the computed steps of one acquisition with their metadata, and keep the history of what was stored.

    Rationale:
    - The service computes steps; where and how they are stored (an HDF5 group per step today) is not its concern.
    - Writing a step then reading it back must give the same values, whatever the storage.

    Design:
    - Outbound port, pure ABC, bound to one acquisition when built; it creates the storage when the acquisition has none (the acquisition exports the CSV only). Saving a step replaces the previous one of the same name.
    - load_step is the read-back that proves the write; an unknown step raises KeyError.
    """

    @abstractmethod
    def record_source(self, source: SourceRecordDTO) -> None:
        """Remember which scan file the steps come from, the hash of what was read, what the acquisition recorded about
        it, and when it was read."""

    @abstractmethod
    def save_raw_scan(self, samples: ScanSamplesDTO) -> None:
        """Store the points as read from the scan file, next to the steps: the file holds its own raw data."""

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
