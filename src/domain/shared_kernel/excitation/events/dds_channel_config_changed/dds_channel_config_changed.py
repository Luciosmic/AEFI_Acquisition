from dataclasses import dataclass

from domain.shared_kernel.events.domain_event import DomainEvent


@dataclass(frozen=True)
class DdsChannelConfigChanged(DomainEvent):
    """Event emitted when a DDS excitation channel's actual gain and/or
    phase register value changes on the AD9106."""

    channel: int
    gain: int
    phase: int
