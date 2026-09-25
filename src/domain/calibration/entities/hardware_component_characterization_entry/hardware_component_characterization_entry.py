"""
Hardware Component Characterization Entry Entity

Responsibility:
- Immutable, append-only record of one characterization of a hardware
  component, identified by its kind and unique name.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

from domain.calibration.value_objects.component_characterization.component_characterization import (
    ComponentCharacterization,
)
from domain.calibration.value_objects.hardware_component_name.hardware_component_name import (
    HardwareComponentName,
)
from domain.calibration.value_objects.hardware_component_kind.hardware_component_kind import (
    HardwareComponentKind,
)


@dataclass(frozen=True)
class HardwareComponentCharacterizationEntry:
    """
    One characterization of the component `component_name` of `kind`.
    Several entries with the same name are that component's history (values
    completed over time); the most recent is current.

    Entity — identity is `entry_id`. Immutable once created.
    """

    entry_id: UUID
    component_name: HardwareComponentName
    characterization: ComponentCharacterization
    recorded_at: datetime

    def __post_init__(self):
        if not self.component_name.strip():
            raise ValueError("component_name must not be empty")

    @property
    def kind(self) -> HardwareComponentKind:
        return self.characterization.kind

    @staticmethod
    def single(
        component_name: HardwareComponentName, characterization: ComponentCharacterization
    ) -> "HardwareComponentCharacterizationEntry":
        return HardwareComponentCharacterizationEntry(
            entry_id=uuid4(),
            component_name=component_name,
            characterization=characterization,
            recorded_at=datetime.now(timezone.utc),
        )
