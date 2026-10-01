from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple


@dataclass(frozen=True)
class EventLogSummaryDTO:
    location: str  # directory holding the session files
    total_size_bytes: int
    session_count: int
    oldest_started_at: Optional[datetime]
    size_warning: bool
    size_warning_threshold_bytes: int
    retention_days: int
    # What delete_expired_sessions() would remove right now:
    expired_session_count: int
    expired_size_bytes: int
    expired_oldest_started_at: Optional[datetime]
    expired_newest_started_at: Optional[datetime]


@dataclass(frozen=True)
class EventLogPurgeResultDTO:
    deleted_session_count: int
    freed_bytes: int
    not_deleted: Tuple[str, ...]  # session names left in place (e.g. file in use)
