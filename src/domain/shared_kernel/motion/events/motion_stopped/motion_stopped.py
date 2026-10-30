from dataclasses import dataclass

from domain.shared_kernel.events.domain_event import DomainEvent


@dataclass(frozen=True)
class MotionStopped(DomainEvent):
    """Event published when motion is stopped (regular stop with deceleration)."""
    reason: str  # e.g., "scan_cancelled", "user_requested"
