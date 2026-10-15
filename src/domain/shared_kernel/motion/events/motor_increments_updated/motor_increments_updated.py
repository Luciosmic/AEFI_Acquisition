from dataclasses import dataclass

from domain.shared_kernel.events.domain_event import DomainEvent


@dataclass(frozen=True)
class MotorIncrementsUpdated(DomainEvent):
    """The motor position of the bench, in increments (pulses counted by the
    controller), changed — published whether or not the mm conversion exists."""

    x_increments: int
    y_increments: int
    is_moving: bool
