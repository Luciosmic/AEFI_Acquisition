"""
Event Bus Motion Synchronizer

Responsibility:
- Implement IMotionSynchronizer by translating domain motion events into a
  blocking wait primitive that returns OperationResult.

Rationale:
- The Application layer scan loop needs to block until a specific motion_id
  reaches a terminal state (completed / failed / stopped / emergency stop).
- Motion completion is signaled asynchronously through the shared IDomainEventBus.
- This adapter bridges the event-driven motion world and the sequential scan
  loop without leaking threading.Event or bus-subscription details upward.

Design:
- Subscribes to the 4 motion event topics at construction.
- Uses one threading.Event + result slot per pending motion_id (dict keyed
  by motion_id so concurrent motions would be safe, though the scan loop
  sends only one at a time).
- EmergencyStopTriggered has no motion_id: it cancels every pending wait.
- Always returns OperationResult — never raises for expected outcomes.
- Unsubscribes on close() to avoid memory leaks in long-lived processes.
"""

from __future__ import annotations

import threading
from typing import Dict, Optional, Tuple

from application.services.scan_application_service.errors.motion_sync_error import (
    EmergencyStop,
    MotionHardwareFailed,
    MotionSyncError,
    MotionStoppedExternally,
    MotionTimeout,
)
from application.services.scan_application_service.ports.i_motion_synchronizer import (
    IMotionSynchronizer,
)
from domain.shared_kernel.events.emergency_stop_triggered.emergency_stop_triggered import (
    EmergencyStopTriggered,
)
from domain.shared_kernel.events.i_domain_event_bus import IDomainEventBus
from domain.shared_kernel.events.motion_completed.motion_completed import MotionCompleted
from domain.shared_kernel.events.motion_failed.motion_failed import MotionFailed
from domain.shared_kernel.events.motion_stopped.motion_stopped import MotionStopped
from domain.shared_kernel.operation_result import OperationResult

# (motion_event, optional_error) stored per pending motion_id
_Slot = Tuple[threading.Event, Optional[MotionSyncError]]


class EventBusMotionSynchronizer(IMotionSynchronizer):
    """Bridges domain motion events into blocking OperationResult waits."""

    def __init__(self, event_bus: IDomainEventBus) -> None:
        self._event_bus = event_bus
        # motion_id -> (threading.Event, result_container)
        # result_container is a list so we can mutate from event handlers
        self._pending: Dict[str, Tuple[threading.Event, list]] = {}
        self._lock = threading.Lock()

        event_bus.subscribe("motioncompleted", self._on_motion_completed)
        event_bus.subscribe("motionfailed", self._on_motion_failed)
        event_bus.subscribe("motionstopped", self._on_motion_stopped)
        event_bus.subscribe("emergencystoptriggered", self._on_emergency_stop)

    # ------------------------------------------------------------------ #
    # IMotionSynchronizer
    # ------------------------------------------------------------------ #

    def wait_for_motion(
        self, motion_id: str, timeout_seconds: float
    ) -> OperationResult[None, MotionSyncError]:
        evt = threading.Event()
        result_container: list = [None]  # [MotionSyncError | None]

        with self._lock:
            self._pending[motion_id] = (evt, result_container)

        try:
            signaled = evt.wait(timeout=timeout_seconds)
        finally:
            with self._lock:
                self._pending.pop(motion_id, None)

        if not signaled:
            return OperationResult.fail(
                MotionTimeout(motion_id=motion_id, timeout_seconds=timeout_seconds)
            )

        error: Optional[MotionSyncError] = result_container[0]
        if error is not None:
            return OperationResult.fail(error)

        return OperationResult.ok(None)

    # ------------------------------------------------------------------ #
    # Event handlers
    # ------------------------------------------------------------------ #

    def _on_motion_completed(self, event: MotionCompleted) -> None:
        self._signal(event.motion_id, error=None)

    def _on_motion_failed(self, event: MotionFailed) -> None:
        self._signal(
            event.motion_id,
            error=MotionHardwareFailed(motion_id=event.motion_id, error_detail=event.error),
        )

    def _on_motion_stopped(self, event: MotionStopped) -> None:
        # MotionStopped has no motion_id — affects the most recently registered pending motion.
        # The scan loop sends one motion at a time, so only one entry exists in _pending.
        with self._lock:
            for mid, (evt, container) in list(self._pending.items()):
                container[0] = MotionStoppedExternally(motion_id=mid, reason=event.reason)
                evt.set()

    def _on_emergency_stop(self, event: EmergencyStopTriggered) -> None:
        with self._lock:
            for mid, (evt, container) in list(self._pending.items()):
                container[0] = EmergencyStop()
                evt.set()

    def _signal(self, motion_id: str, error: Optional[MotionSyncError]) -> None:
        with self._lock:
            entry = self._pending.get(motion_id)
        if entry is None:
            return
        evt, container = entry
        container[0] = error
        evt.set()

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    def close(self) -> None:
        """Unsubscribe from the event bus (call on application shutdown)."""
        self._event_bus.unsubscribe("motioncompleted", self._on_motion_completed)
        self._event_bus.unsubscribe("motionfailed", self._on_motion_failed)
        self._event_bus.unsubscribe("motionstopped", self._on_motion_stopped)
        self._event_bus.unsubscribe("emergencystoptriggered", self._on_emergency_stop)
