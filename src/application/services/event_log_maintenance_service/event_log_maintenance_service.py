import logging
from datetime import datetime, timedelta, timezone
from typing import Callable, List

from application.services.event_log_maintenance_service.dtos.event_log_dto import (
    EventLogPurgeResultDTO,
    EventLogSummaryDTO,
)
from application.services.event_log_maintenance_service.i_api_event_log_maintenance_service import (
    IApiEventLogMaintenanceService,
)
from application.services.event_log_maintenance_service.ports.i_event_log_storage_port import (
    IEventLogStoragePort,
    StoredEventLogSession,
)

# ponytail: constants, not config — move to .aefi_acquisition/configs/ the day a bench needs other values.
RETENTION = timedelta(days=90)
SIZE_WARNING_BYTES = 20 * 1024**3  # 20 Go, as Windows Explorer counts them

logger = logging.getLogger(__name__)


class EventLogMaintenanceService(IApiEventLogMaintenanceService):
    """
    Shows how much room the event audit log takes, and deletes its sessions
    older than RETENTION — only when the user asks (see intention.md).
    """

    def __init__(self, storage: IEventLogStoragePort, now: Callable[[], datetime] = lambda: datetime.now(timezone.utc)):
        self._storage = storage
        self._now = now

    # -- commands -----------------------------------------------------------------

    def delete_expired_sessions(self) -> EventLogPurgeResultDTO:
        logger.info("EventLogMaintenanceService: Command delete_expired_sessions retention_days=%d", RETENTION.days)
        expired = self._expired(self._storage.list_sessions())
        if not expired:
            logger.info("EventLogMaintenanceService: no session older than %d days. Doing nothing.", RETENTION.days)
            return EventLogPurgeResultDTO(0, 0, ())

        deleted: List[StoredEventLogSession] = []
        not_deleted: List[str] = []
        for session in expired:
            result = self._storage.delete_session(session.name)
            if result.is_success:
                deleted.append(session)
            else:
                logger.warning(
                    "EventLogMaintenanceService: session %s not deleted (%s), left in place",
                    session.name,
                    result.error.reason,
                )
                not_deleted.append(session.name)

        freed = sum(s.size_bytes for s in deleted)
        if deleted:
            logger.info(
                "EventLogMaintenanceService: deleted %d event log session(s) started %s .. %s, freed_bytes=%d",
                len(deleted),
                min(s.started_at for s in deleted).isoformat(),
                max(s.started_at for s in deleted).isoformat(),
                freed,
            )
        return EventLogPurgeResultDTO(len(deleted), freed, tuple(not_deleted))

    # -- queries ------------------------------------------------------------------

    def get_summary(self) -> EventLogSummaryDTO:
        sessions = self._storage.list_sessions()
        expired = self._expired(sessions)
        total = sum(s.size_bytes for s in sessions)
        return EventLogSummaryDTO(
            location=self._storage.location(),
            total_size_bytes=total,
            session_count=len(sessions),
            oldest_started_at=min((s.started_at for s in sessions), default=None),
            size_warning=total >= SIZE_WARNING_BYTES,
            size_warning_threshold_bytes=SIZE_WARNING_BYTES,
            retention_days=RETENTION.days,
            expired_session_count=len(expired),
            expired_size_bytes=sum(s.size_bytes for s in expired),
            expired_oldest_started_at=min((s.started_at for s in expired), default=None),
            expired_newest_started_at=max((s.started_at for s in expired), default=None),
        )

    def _expired(self, sessions: List[StoredEventLogSession]) -> List[StoredEventLogSession]:
        cutoff = self._now() - RETENTION
        return [s for s in sessions if not s.is_live and s.started_at < cutoff]
