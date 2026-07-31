from dataclasses import dataclass

from domain.shared_kernel.events.domain_event import DomainEvent


@dataclass(frozen=True)
class ExcitationLevelsChanged(DomainEvent):
    """Event emitted when either DDS excitation level (S1-S2 or S3-S4) actually changes."""

    level_s1_s2_percent: float
    level_s3_s4_percent: float
