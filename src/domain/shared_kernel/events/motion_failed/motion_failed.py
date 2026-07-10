from dataclasses import dataclass

from domain.shared_kernel.events.domain_event import DomainEvent


@dataclass(frozen=True)
class MotionFailed(DomainEvent):
    """Event published when a motion fails."""
    motion_id: str
    error: str
