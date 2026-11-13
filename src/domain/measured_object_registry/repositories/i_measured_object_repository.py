from abc import ABC, abstractmethod
from typing import List, Sequence

from domain.measured_object_registry.entities.measured_object.measured_object import MeasuredObject
from domain.shared_kernel.operation_result import OperationResult


class IMeasuredObjectRepository(ABC):
    """
    Responsibility:
    - Persist the measured_objects of the registry and read them back.

    Rationale:
    - The registry must survive restarts; the domain stays free of storage.

    Design:
    - Expected failures (registry unreadable / not writable) are results,
      never exceptions; the reason is a readable string.
    - An unreadable registry is a failure, never an empty list: adding to
      it afterwards would overwrite the measured_objects it holds.
    """

    @abstractmethod
    def find_all(self) -> OperationResult[List[MeasuredObject], str]: ...

    @abstractmethod
    def add(self, measured_object: MeasuredObject) -> OperationResult[None, str]: ...

    @abstractmethod
    def save_all(self, measured_objects: Sequence[MeasuredObject]) -> OperationResult[None, str]:
        """Replace the registry by these measured_objects (after a rename or a deletion)."""
