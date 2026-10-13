from dataclasses import dataclass
from typing import Optional

from domain.shared_kernel.events.domain_event import DomainEvent


@dataclass(frozen=True)
class MotionConversionFoundMissing(DomainEvent):
    """Event published when the mm/pulse conversion cannot be derived (mechanical
    transmission not calibrated): motion stays refused until it is."""

    motor_name: Optional[str]
    missing_quantity: str
    where_to_enter: str
