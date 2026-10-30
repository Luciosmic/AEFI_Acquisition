from dataclasses import dataclass

from domain.shared_kernel.events.domain_event import DomainEvent


@dataclass(frozen=True)
class EmergencyStopTriggered(DomainEvent):
    """Event published when emergency stop is triggered (immediate halt)."""
    pass
