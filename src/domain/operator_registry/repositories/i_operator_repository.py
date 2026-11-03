from abc import ABC, abstractmethod
from typing import List

from domain.operator_registry.entities.operator.operator import Operator
from domain.shared_kernel.operation_result import OperationResult


class IOperatorRepository(ABC):
    """
    Responsibility:
    - Persist the operators of the registry and read them back.

    Rationale:
    - The registry must survive restarts; the domain stays free of storage.

    Design:
    - Expected failures (registry unreadable / not writable) are results,
      never exceptions; the reason is a readable string.
    - An unreadable registry is a failure, never an empty list: adding to
      it afterwards would overwrite the operators it holds.
    """

    @abstractmethod
    def find_all(self) -> OperationResult[List[Operator], str]: ...

    @abstractmethod
    def add(self, operator: Operator) -> OperationResult[None, str]: ...
