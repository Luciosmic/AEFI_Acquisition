from dataclasses import dataclass

from domain.shared_kernel.events.domain_event import DomainEvent


@dataclass(frozen=True)
class SystemShuttingDownEvent(DomainEvent):
    """Event emitted when the system shutdown sequence begins."""

    message: str = "System shutting down"
