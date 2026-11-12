"""ColumnRestMeasured event (see column_rest_measured_intention.md)."""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from domain.shared_kernel.events.domain_event import DomainEvent


@dataclass(frozen=True)
class ColumnRestMeasured(DomainEvent):
    """The rest level of the still column was measured (or could not be) before the first move.

    Units (UCUM): rest_vibration_g and the threshold `[g]`, durations `s`, factor `1`.
    rest_vibration_g None: the scan settles every point on the fixed delay (unavailable_reason says why).
    The criterion travels with the fact, so the event is readable without the code that judged it.
    """

    scan_id: UUID
    rest_vibration_g: Optional[float]
    sample_count: int
    unavailable_reason: Optional[str]
    rest_measurement_s: float
    window_s: float
    factor: float
    timeout_s: float
    minimum_delay_s: float
