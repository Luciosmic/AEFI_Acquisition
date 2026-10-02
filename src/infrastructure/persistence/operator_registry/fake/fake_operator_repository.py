"""
Fake Operator Repository — in-memory registry for tests
(see fake_operator_repository_intention.md).
"""

from typing import List, Optional, Sequence

from domain.operator_registry.entities.operator.operator import Operator
from domain.operator_registry.repositories.i_operator_repository import IOperatorRepository
from domain.shared_kernel.operation_result import OperationResult


class FakeOperatorRepository(IOperatorRepository):
    """Holds operators in memory. `read_failure` / `write_failure` reproduce
    the real repository's failures (unreadable / not writable registry)."""

    def __init__(
        self, operators: Sequence[Operator] = (), read_failure: Optional[str] = None, write_failure: Optional[str] = None,
    ) -> None:
        self.operators: List[Operator] = list(operators)
        self.read_failure = read_failure
        self.write_failure = write_failure

    def find_all(self) -> OperationResult[List[Operator], str]:
        if self.read_failure is not None:
            return OperationResult.fail(self.read_failure)
        return OperationResult.ok(list(self.operators))

    def add(self, operator: Operator) -> OperationResult[None, str]:
        if self.read_failure is not None:  # like the real one: never writes over an unread registry
            return OperationResult.fail(self.read_failure)
        if self.write_failure is not None:
            return OperationResult.fail(self.write_failure)
        self.operators.append(operator)
        return OperationResult.ok(None)
