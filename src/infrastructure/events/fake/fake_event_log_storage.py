from typing import Iterable, List

from application.services.event_log_maintenance_service.ports.i_event_log_storage_port import (
    EventLogSessionNotDeleted,
    IEventLogStoragePort,
    StoredEventLogSession,
)
from domain.shared_kernel.operation_result import OperationResult


class FakeEventLogStorage(IEventLogStoragePort):
    """In-memory event log sessions. `locked` names refuse deletion, like a
    file still open in another app instance on Windows."""

    def __init__(
        self, sessions: Iterable[StoredEventLogSession] = (), locked: Iterable[str] = (), location: str = "fake://events"
    ):
        self.sessions = {s.name: s for s in sessions}
        self._locked = set(locked)
        self._location = location

    def location(self) -> str:
        return self._location

    def list_sessions(self) -> List[StoredEventLogSession]:
        return sorted(self.sessions.values(), key=lambda s: s.started_at)

    def delete_session(self, name: str) -> OperationResult[None, EventLogSessionNotDeleted]:
        session = self.sessions.get(name)
        if session is None:
            return OperationResult.fail(EventLogSessionNotDeleted(name, "no such session"))
        if session.is_live:
            return OperationResult.fail(EventLogSessionNotDeleted(name, "live session"))
        if name in self._locked:
            return OperationResult.fail(EventLogSessionNotDeleted(name, "file in use"))
        del self.sessions[name]
        return OperationResult.ok(None)
