from dataclasses import dataclass
from uuid import UUID

from domain.shared_kernel.events.domain_event import DomainEvent


@dataclass(frozen=True)
class InertialSensorStreamFailed(DomainEvent):
    """The inertial sensor stream stopped on a failure (not on an operator stop)."""

    acquisition_id: UUID
    reason: str
