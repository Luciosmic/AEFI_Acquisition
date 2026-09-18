from dataclasses import dataclass

from domain.shared_kernel.events.domain_event import DomainEvent


@dataclass(frozen=True)
class ExcitationDdsLinkChanged(DomainEvent):
    """Event emitted when the DDS1/DDS2 excitation gain link toggle
    (S1-S2 = S3-S4) actually changes."""

    linked: bool
