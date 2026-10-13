"""Bounded in-memory tail of the domain events, for read-only observation.

Rationale: the JSONL audit log is the durable trace but is not queryable
from a running app; an observer (MCP) needs "what just happened" without
reading files. `record` runs in the publisher's thread on the hot path, so
it stores only a light tuple — no serialization, no `asdict`.
"""

import threading
import time
from collections import deque
from datetime import datetime, timezone
from typing import Any, Deque, Dict, Iterable, List, Optional, Tuple

# High-frequency types (several per second during acquisition/motion) that would flush the buffer.
DEFAULT_EXCLUDED_EVENT_TYPES = frozenset({"aefivoltagesampleacquired", "positionupdated"})
DEFAULT_MAXLEN = 1000
_MAX_SUMMARY_FIELDS = 8
_MAX_VALUE_CHARS = 80


class EventRingBuffer:
    """Subscribe `record` to the bus wildcard "*"; read with `recent`."""

    def __init__(
        self,
        maxlen: int = DEFAULT_MAXLEN,
        excluded_event_types: Iterable[str] = DEFAULT_EXCLUDED_EVENT_TYPES,
    ):
        self._excluded = frozenset(t.lower() for t in excluded_event_types)
        # (event_type lowercase class name, epoch seconds, ((field, value), ...))
        self._events: Deque[Tuple[str, float, tuple]] = deque(maxlen=maxlen)
        self._lock = threading.Lock()

    def record(self, event: Any) -> None:
        event_type = type(event).__name__.lower()
        if event_type in self._excluded:
            return
        occurred_on = getattr(event, "occurred_on", None)
        epoch = occurred_on.timestamp() if isinstance(occurred_on, datetime) else time.time()
        fields = getattr(event, "__dict__", None) or {}
        summary = []
        for key, value in fields.items():
            if len(summary) >= _MAX_SUMMARY_FIELDS:
                break
            if key == "occurred_on":
                continue
            if isinstance(value, (bool, int, float)) or value is None:
                summary.append((key, value))
            elif isinstance(value, str):
                summary.append((key, value[:_MAX_VALUE_CHARS]))
            else:  # UUID, enum, nested value objects: truncated str is enough to orient
                summary.append((key, str(value)[:_MAX_VALUE_CHARS]))
        with self._lock:
            self._events.append((event_type, epoch, tuple(summary)))

    def recent(
        self,
        event_type: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """The last `limit` matching events, oldest first. `event_type` is the
        bus topic (lowercase class name) and is matched case-insensitively."""
        wanted = event_type.lower() if event_type else None
        since_epoch = since.timestamp() if since is not None else None
        with self._lock:
            snapshot = list(self._events)
        matching = [
            e for e in snapshot
            if (wanted is None or e[0] == wanted) and (since_epoch is None or e[1] >= since_epoch)
        ]
        if limit > 0:
            matching = matching[-limit:]
        return [
            {
                "event_type": etype,
                "occurred_on": datetime.fromtimestamp(epoch, timezone.utc).isoformat(),
                "summary": dict(summary),
            }
            for etype, epoch, summary in matching
        ]
