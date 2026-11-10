from dataclasses import dataclass
from uuid import UUID

from domain.shared_kernel.events.domain_event import DomainEvent


@dataclass(frozen=True)
class InertialProbeStreamFailed(DomainEvent):
    """The inertial probe stream stopped on a failure (not on an operator stop)."""

    acquisition_id: UUID
    reason: str
