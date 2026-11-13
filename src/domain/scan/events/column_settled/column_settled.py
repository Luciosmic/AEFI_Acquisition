"""ColumnSettled event (see column_settled_intention.md)."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from domain.shared_kernel.events.domain_event.domain_event import DomainEvent

# How the wait ended.
SETTLED_ON_ACCELEROMETER = "accelerometer"  # the column came back to rest
SETTLED_ON_FIXED_DELAY = "fixed_delay"  # accelerometer unusable: the fixed delay alone
SETTLED_ON_TIMEOUT = "timeout"  # still vibrating past the timeout: measured anyway
SETTLE_INTERRUPTED = "interrupted"  # the scan was cancelled or failed during the wait


@dataclass(frozen=True)
class ColumnSettled(DomainEvent):
    """The wait after a move ended, before the point `point_index` was measured.

    Units (UCUM): waited_s `s`, vibration_g and threshold_g `[g]` (None when not judged).
    stopped_at: end of the move (host clock, with offset). In a fly scan the wait is at
    the start of a line, before its first point.
    """

    scan_id: UUID
    point_index: int
    method: str
    stopped_at: datetime
    waited_s: float
    vibration_g: Optional[float] = None
    threshold_g: Optional[float] = None
