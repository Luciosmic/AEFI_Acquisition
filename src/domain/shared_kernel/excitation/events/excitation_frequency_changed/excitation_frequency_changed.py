from dataclasses import dataclass

from domain.shared_kernel.events.domain_event import DomainEvent


@dataclass(frozen=True)
class ExcitationFrequencyChanged(DomainEvent):
    """Event emitted when the DDS excitation frequency actually changes."""

    frequency_hz: float
