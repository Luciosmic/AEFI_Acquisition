import json
import logging
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)

# Session file = events_<SESSION_TIMESTAMP_FORMAT, UTC start>_<6 hex>.jsonl — also parsed by FileEventLogStorage.
SESSION_TIMESTAMP_FORMAT = "%Y%m%dT%H%M%SZ"


def _json_default(value: Any) -> Any:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def serialize_event(event: Any) -> str:
    """One JSONL line: `event_type` + the event's fields. Shared with the
    per-scan event export so both files use the same format."""
    payload = asdict(event) if is_dataclass(event) else {"data": event}
    return json.dumps({"event_type": type(event).__name__, **payload}, default=_json_default)


class EventAuditLog:
    """Appends every domain event it receives to a JSONL file, one file per app run."""

    def __init__(self, log_dir: Path):
        log_dir.mkdir(parents=True, exist_ok=True)
        session_start = datetime.now(timezone.utc).strftime(SESSION_TIMESTAMP_FORMAT)
        self._path = log_dir / f"events_{session_start}_{uuid4().hex[:6]}.jsonl"

    @property
    def path(self) -> Path:
        """This run's session file (created on the first recorded event)."""
        return self._path

    def record(self, event: Any) -> None:
        try:
            line = serialize_event(event)
        except Exception:
            logger.exception("EventAuditLog: failed to serialize event %r", type(event).__name__)
            return

        with self._path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
