"""
Hardware Component Selection Entity

Responsibility:
- Immutable, append-only record of one mounting: "this component (kind +
  unique name) was mounted on the bench", at a given time. Each mounting has
  its own identity.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

from domain.calibration.value_objects.hardware_component_name.hardware_component_name import (
    HardwareComponentName,
)
from domain.calibration.value_objects.hardware_component_kind.hardware_component_kind import (
    HardwareComponentKind,
)


@dataclass(frozen=True)
class HardwareComponentSelection:
    """
    One mounting in a kind's mounting log; the latest one is the current
    mounting. `mounting_id` identifies this mounting — calibrations that
    depend on how the component is physically mounted (sensor angles)
    reference it: unmounting and remounting the same component is a new
    mounting, with a new identity.
    """

    kind: HardwareComponentKind
    component_name: HardwareComponentName
    selected_at: datetime
    mounting_id: UUID

    def __post_init__(self):
        if not self.component_name.strip():
            raise ValueError("component_name must not be empty")

    @staticmethod
    def now(kind: HardwareComponentKind, component_name: HardwareComponentName) -> "HardwareComponentSelection":
        return HardwareComponentSelection(
            kind=kind,
            component_name=component_name,
            selected_at=datetime.now(timezone.utc),
            mounting_id=uuid4(),
        )
