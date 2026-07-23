"""
Motion Synchronizer Port

Responsibility:
- Provide the scan loop with a blocking-until-motion-completes primitive
  that returns a typed OperationResult instead of raising.

Rationale:
- The motion port is fire-and-forget: `move_to(position) -> motion_id`.
  Motion completion is signaled asynchronously through domain events on
  the shared bus (MotionCompleted, MotionFailed, MotionStopped,
  EmergencyStopTriggered).
- The scan use-case loop lives in the Application layer and must not
  know that motion completion arrives through an event bus, nor that
  the underlying primitive is a threading.Event. Both are Infrastructure
  concerns.
- This port isolates the "wait for a specific motion_id to complete"
  operation behind an application-owned contract.

Design:
- Single method: wait_for_motion(motion_id, timeout) -> OperationResult.
- Returns typed MotionSyncError on failure (Timeout / HardwareFailed /
  EmergencyStop / StoppedExternally) — never raises for expected outcomes.
- Timeout is configurable per call because different motion segments have
  different physical durations.
- The implementation is expected to subscribe to motion events at
  construction and clean up subscribers on shutdown; the port itself
  does not expose subscribe/unsubscribe (Infrastructure concern).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from application.services.scan_application_service.errors.motion_sync_error import (
    MotionSyncError,
)
from domain.shared_kernel.operation_result import OperationResult


class IMotionSynchronizer(ABC):
    """
    Port for synchronizing the scan loop with asynchronous motion completion.
    """

    @abstractmethod
    def wait_for_motion(
        self, motion_id: str, timeout_seconds: float
    ) -> OperationResult[None, MotionSyncError]:
        """
        Block until the motion identified by motion_id reaches a terminal state
        (completed, failed, stopped, or aborted by emergency stop) or the
        timeout expires.

        Returns:
            OperationResult.ok(None) when the motion completed normally.
            OperationResult.fail(MotionSyncError.*) for every other terminal
            outcome. Never raises for expected outcomes.
        """
