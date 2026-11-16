from abc import ABC, abstractmethod
from typing import List

from ..dtos.stored_step_dto import StoredStepDTO


class IStepReader(ABC):
    """
    Responsibility:
    - Tell which processing steps an acquisition file holds, and read one back as stored.

    Rationale:
    - The map service decodes and arranges what was stored; where the steps live and in which format is the storage's concern.
    - What the step writer stored must read back with the same values.

    Design:
    - Outbound port, pure ABC, read-only. A file that does not exist or cannot be read holds no step (empty list).
    - Reading a step of a missing file raises FileNotFoundError; reading a step never stored raises KeyError.
    """

    @abstractmethod
    def list_steps(self, acquisition_file: str) -> List[str]:
        """The names of the steps stored in the file, empty when the file is missing or unreadable."""

    @abstractmethod
    def read_step(self, acquisition_file: str, step_name: str) -> StoredStepDTO:
        """The array and the metadata of a stored step, as stored."""
