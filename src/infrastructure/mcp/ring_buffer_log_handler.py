"""Logging handler keeping the last N log lines in memory, for read-only observation.

Rationale: logs otherwise reach only the UI panel (stdout is swallowed) or an
opt-in file. An observer (MCP) needs the recent tail from the running app.
The handler never logs itself (re-entrancy) and stores light tuples, not LogRecords.
"""

import logging
import threading
from collections import deque
from datetime import datetime, timezone
from typing import Any, Deque, Dict, List, Optional, Tuple

DEFAULT_MAXLEN = 2000
_MAX_MESSAGE_CHARS = 500


class RingBufferLogHandler(logging.Handler):
    def __init__(self, maxlen: int = DEFAULT_MAXLEN, level: int = logging.INFO):
        super().__init__(level=level)
        # (created epoch, levelname, logger name, truncated message)
        self._lines: Deque[Tuple[float, str, str, str]] = deque(maxlen=maxlen)
        self._buffer_lock = threading.Lock()

    def emit(self, record: logging.LogRecord) -> None:
        try:
            line = (record.created, record.levelname, record.name, record.getMessage()[:_MAX_MESSAGE_CHARS])
            with self._buffer_lock:
                self._lines.append(line)
        except Exception:
            pass  # never log from here: it would re-enter this handler

    def recent(
        self,
        level: str = "INFO",
        logger_prefix: Optional[str] = None,
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        """The last `limit` lines at or above `level`, oldest first."""
        threshold = logging.getLevelName(level.upper())
        if not isinstance(threshold, int):
            threshold = logging.INFO
        with self._buffer_lock:
            snapshot = list(self._lines)
        matching = [
            line for line in snapshot
            if logging.getLevelName(line[1]) >= threshold
            and (not logger_prefix or line[2].startswith(logger_prefix))
        ]
        if limit > 0:
            matching = matching[-limit:]
        return [
            {
                "time": datetime.fromtimestamp(created, timezone.utc).isoformat(),
                "level": levelname,
                "logger": name,
                "message": message,
            }
            for created, levelname, name, message in matching
        ]
