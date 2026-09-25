from dataclasses import dataclass
from uuid import UUID

from domain.shared_kernel.events.domain_event import DomainEvent
from domain.calibration.entities.hardware_component_characterization_entry.hardware_component_characterization_entry import (
    HardwareComponentCharacterizationEntry,
)
from domain.calibration.value_objects.hardware_component_kind.hardware_component_kind import (
    HardwareComponentKind,
)


@dataclass(frozen=True)
class HardwareComponentCharacterized(DomainEvent):
    """A characterization entry was recorded for a hardware component."""

    entry: HardwareComponentCharacterizationEntry


@dataclass(frozen=True)
class HardwareComponentMounted(DomainEvent):
    """A hardware component was declared mounted on the bench."""

    kind: HardwareComponentKind
    component_name: str
    mounting_id: UUID
