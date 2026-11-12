"""
Fake MeasuredObject Repository — in-memory registry for tests
(see fake_measured_object_repository_intention.md).
"""

from typing import List, Optional, Sequence

from domain.measured_object_registry.entities.measured_object.measured_object import MeasuredObject
from domain.measured_object_registry.repositories.i_measured_object_repository import IMeasuredObjectRepository
from domain.shared_kernel.operation_result import OperationResult


class FakeMeasuredObjectRepository(IMeasuredObjectRepository):
    """Holds measured_objects in memory. `read_failure` / `write_failure` reproduce
    the real repository's failures (unreadable / not writable registry)."""

    def __init__(
        self, measured_objects: Sequence[MeasuredObject] = (), read_failure: Optional[str] = None, write_failure: Optional[str] = None,
    ) -> None:
        self.measured_objects: List[MeasuredObject] = list(measured_objects)
        self.read_failure = read_failure
        self.write_failure = write_failure

    def find_all(self) -> OperationResult[List[MeasuredObject], str]:
        if self.read_failure is not None:
            return OperationResult.fail(self.read_failure)
        return OperationResult.ok(list(self.measured_objects))

    def add(self, measured_object: MeasuredObject) -> OperationResult[None, str]:
        if self.read_failure is not None:  # like the real one: never writes over an unread registry
            return OperationResult.fail(self.read_failure)
        if self.write_failure is not None:
            return OperationResult.fail(self.write_failure)
        self.measured_objects.append(measured_object)
        return OperationResult.ok(None)
