from dataclasses import dataclass

from domain.shared_kernel.events.domain_event import DomainEvent


@dataclass(frozen=True)
class SystemStartupFailedEvent(DomainEvent):
    """Event emitted when the system fails to start."""

    reason: str
