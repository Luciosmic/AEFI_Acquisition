from dataclasses import dataclass

from domain.shared_kernel.events.domain_event import DomainEvent


@dataclass(frozen=True)
class SystemShutdownCompleteEvent(DomainEvent):
    """Event emitted when the system shutdown sequence completes."""

    success: bool
    details: str = ""
