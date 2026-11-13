"""
Fake Event Bus Motion Synchronizer

Responsibility:
- Implement IMotionSynchronizer for tests with pre-programmed result sequences
  that reproduce every MotionSyncError variant the Real adapter can return.

Rationale:
- The real EventBusMotionSynchronizer blocks until motion events arrive on the
  bus. In unit tests the motion hardware is absent, so the real adapter would
  time out on every call.
- Injecting pre-programmed OperationResult values lets each test exercise a
  specific code path (success, timeout, hardware failure, emergency stop,
  externally stopped) without any bus or thread involvement.

Design:
- Constructor accepts a list of OperationResult values (the "program").
- Each wait_for_motion() call pops the next result from the list.
- If the list is exhausted, raises IndexError — a test that sends more
  motions than it programmed for is a test bug, not a production scenario.
- call_count tracks how many times wait_for_motion was called (useful for
  asserting that a cancelled scan stopped issuing motions).
"""

from __future__ import annotations

from typing import List

from application.services.scan_application_service.errors.motion_sync_error import (
    MotionSyncError,
)
from application.services.scan_application_service.ports.i_motion_synchronizer import (
    IMotionSynchronizer,
)
from domain.shared_kernel.operation_result import OperationResult


class FakeEventBusMotionSynchronizer(IMotionSynchronizer):
    """
    Configurable motion synchronizer for tests.

    Usage::

        sync = FakeEventBusMotionSynchronizer([
            OperationResult.ok(None),                         # point 0: success
            OperationResult.fail(MotionTimeout("id1", 30.0)), # point 1: timeout
        ])
    """

    def __init__(self, results: List[OperationResult]) -> None:
        self._results = list(results)
        self.call_count = 0
        self.received_motion_ids: List[str] = []

    def wait_for_motion(
        self, motion_id: str, timeout_seconds: float
    ) -> OperationResult[None, MotionSyncError]:
        if not self._results:
            raise IndexError(
                f"FakeEventBusMotionSynchronizer: no more programmed results "
                f"(call #{self.call_count + 1}, motion_id={motion_id!r}). "
                f"Add more OperationResult entries to the constructor."
            )
        self.call_count += 1
        self.received_motion_ids.append(motion_id)
        return self._results.pop(0)
