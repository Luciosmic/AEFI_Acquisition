from dataclasses import dataclass

from domain.shared_kernel.events.domain_event import DomainEvent


@dataclass(frozen=True)
class SystemReadyEvent(DomainEvent):
    """Event emitted when the system startup sequence completes successfully."""

    message: str = "System is ready"
