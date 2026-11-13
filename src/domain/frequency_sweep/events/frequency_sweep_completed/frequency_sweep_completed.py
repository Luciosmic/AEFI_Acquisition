"""FrequencySweepCompleted event (see frequency_sweep_completed_intention.md)."""

from dataclasses import dataclass

from domain.frequency_sweep.value_objects.frequency_sweep_id.frequency_sweep_id import FrequencySweepId
from domain.shared_kernel.events.domain_event.domain_event import DomainEvent


@dataclass(frozen=True)
class FrequencySweepCompleted(DomainEvent):
    frequency_sweep_id: FrequencySweepId
    role: str
    frequency_count: int
