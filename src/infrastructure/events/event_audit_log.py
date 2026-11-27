import atexit
import json
import logging
import queue
import threading
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Optional, TextIO
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)

# Session file = events_<SESSION_TIMESTAMP_FORMAT, UTC start>_<6 hex>.jsonl — also parsed by FileEventLogStorage.
SESSION_TIMESTAMP_FORMAT = "%Y%m%dT%H%M%SZ"

_STOP = object()  # sentinel: the writer thread ends after the events queued before it


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
    """Appends every domain event it receives to a JSONL file, one file per app run.

    record() only queues the event: the bus publishes from the acquisition
    thread, which must not wait on the disk (one file open per event cost
    ~0.55 ms, three events per acquired point). A single writer thread holds
    the file open, serializes, writes and flushes after each batch.
    """

    def __init__(self, log_dir: Path):
        log_dir.mkdir(parents=True, exist_ok=True)
        session_start = datetime.now(timezone.utc).strftime(SESSION_TIMESTAMP_FORMAT)
        self._path = log_dir / f"events_{session_start}_{uuid4().hex[:6]}.jsonl"
        self._queue: "queue.Queue[Any]" = queue.Queue()
        self._file: Optional[TextIO] = None
        self._closed = False
        self._writer = threading.Thread(target=self._write_loop, name="EventAuditLogWriter", daemon=True)
        self._writer.start()
        atexit.register(self.close)

    @property
    def path(self) -> Path:
        """This run's session file (created on the first recorded event)."""
        return self._path

    def record(self, event: Any) -> None:
        """Queue the event for the writer thread; never blocks on the disk."""
        if not self._closed:
            self._queue.put(event)

    def flush(self) -> None:
        """Block until every event recorded so far is written and flushed."""
        self._queue.join()

    def close(self) -> None:
        """Write what is queued, then stop the writer and close the file."""
        if self._closed:
            return
        self._closed = True
        self._queue.put(_STOP)
        self._writer.join(timeout=5.0)

    def _write_loop(self) -> None:
        while True:
            batch = [self._queue.get()]
            try:
                while True:
                    batch.append(self._queue.get_nowait())
            except queue.Empty:
                pass
            stop = self._write_batch(batch)
            for _ in batch:
                self._queue.task_done()
            if stop:
                if self._file is not None:
                    self._file.close()
                return

    def _write_batch(self, batch: list) -> bool:
        """Write the batch's lines, flush once; True if the stop sentinel came."""
        lines = []
        stop = False
        for event in batch:
            if event is _STOP:
                stop = True
                continue
            try:
                lines.append(serialize_event(event) + "\n")
            except Exception:
                logger.exception("EventAuditLog: failed to serialize event %r", type(event).__name__)
        if lines:
            try:
                if self._file is None:
                    self._file = self._path.open("a", encoding="utf-8")
                self._file.writelines(lines)
                self._file.flush()
            except Exception:  # the writer must survive, or flush() would wait forever
                logger.exception("EventAuditLog: failed to write %d event(s) to %s", len(lines), self._path)
        return stop
