import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from application.services.event_log_maintenance_service.ports.i_event_log_storage_port import (
    EventLogSessionNotDeleted,
    IEventLogStoragePort,
    StoredEventLogSession,
)
from domain.shared_kernel.operation_result import OperationResult
from infrastructure.events.event_audit_log import SESSION_TIMESTAMP_FORMAT

_SESSION_NAME = re.compile(r"^events_(\d{8}T\d{6}Z)_[0-9a-f]+\.jsonl$")

logger = logging.getLogger(__name__)


class FileEventLogStorage(IEventLogStoragePort):
    """The EventAuditLog session files of one directory."""

    def __init__(self, log_dir: Path, live_session: Path):
        self._dir = log_dir
        self._live_name = live_session.name

    def list_sessions(self) -> List[StoredEventLogSession]:
        sessions = []
        for path in self._dir.glob("events_*.jsonl"):
            started_at = self._started_at(path.name)
            if started_at is None:
                continue
            try:
                size = path.stat().st_size
            except OSError:  # deleted meanwhile
                continue
            sessions.append(StoredEventLogSession(path.name, started_at, size, path.name == self._live_name))
        return sorted(sessions, key=lambda s: s.started_at)

    def delete_session(self, name: str) -> OperationResult[None, EventLogSessionNotDeleted]:
        if name == self._live_name:
            return self._refuse(name, "live session")
        if self._started_at(name) is None:  # also rejects any path component
            return self._refuse(name, "not an event log session")
        try:
            (self._dir / name).unlink()
        except OSError as e:
            return self._refuse(name, f"{type(e).__name__}: {e}")
        logger.info("FileEventLogStorage: deleted event log session %s", name)
        return OperationResult.ok(None)

    @staticmethod
    def _started_at(name: str):
        match = _SESSION_NAME.match(name)
        if match is None:
            return None
        try:
            return datetime.strptime(match.group(1), SESSION_TIMESTAMP_FORMAT).replace(tzinfo=timezone.utc)
        except ValueError:  # e.g. month 13
            return None

    @staticmethod
    def _refuse(name: str, reason: str) -> OperationResult[None, EventLogSessionNotDeleted]:
        logger.warning("FileEventLogStorage: refused to delete %s (%s)", name, reason)
        return OperationResult.fail(EventLogSessionNotDeleted(name, reason))
