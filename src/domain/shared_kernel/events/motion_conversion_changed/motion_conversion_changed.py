from dataclasses import dataclass
from typing import Optional

from domain.shared_kernel.events.domain_event.domain_event import DomainEvent


@dataclass(frozen=True)
class MotionConversionChanged(DomainEvent):
    """Event published when an already applied mm/pulse conversion was replaced
    by a new one (recalibration, no restart): the same pulse positions now read
    as different millimetres."""

    previous_microns_per_pulse: Optional[float]
    microns_per_pulse: float
    motor_name: str
    stepper_driver_name: str
