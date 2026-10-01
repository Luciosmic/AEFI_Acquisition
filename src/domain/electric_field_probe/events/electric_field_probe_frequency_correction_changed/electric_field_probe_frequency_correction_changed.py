from dataclasses import dataclass
from typing import Optional

from domain.shared_kernel.events.domain_event import DomainEvent


@dataclass(frozen=True)
class ElectricFieldProbeFrequencyCorrectionChanged(DomainEvent):
    """Event emitted whenever a frequency correction is requested on the probe,
    whether it was applied, out of the probe's qualified range, or failed."""

    requested_hz: float
    applied_hz: Optional[float]
    in_range: bool
    error: Optional[str] = None
