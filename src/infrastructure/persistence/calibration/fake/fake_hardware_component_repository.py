"""
Fake Hardware Component Repository

Responsibility:
- Implement `IHardwareComponentRepository` purely in memory, for
  application-layer tests that must not depend on file I/O.
"""

from __future__ import annotations

from typing import List

from domain.calibration.entities.hardware_component_characterization_entry.hardware_component_characterization_entry import (
    HardwareComponentCharacterizationEntry,
)
from domain.calibration.entities.hardware_component_selection.hardware_component_selection import (
    HardwareComponentSelection,
)
from domain.calibration.repositories.i_hardware_component_repository import IHardwareComponentRepository
from domain.calibration.value_objects.hardware_component_kind.hardware_component_kind import (
    HardwareComponentKind,
)


class FakeHardwareComponentRepository(IHardwareComponentRepository):
    """In-memory, append-only catalog + mounting log for tests."""

    def __init__(self):
        self._entries: List[HardwareComponentCharacterizationEntry] = []
        self._selections: List[HardwareComponentSelection] = []

    def add(self, entry: HardwareComponentCharacterizationEntry) -> None:
        self._entries.append(entry)

    def find_all(self, kind: HardwareComponentKind) -> List[HardwareComponentCharacterizationEntry]:
        return [entry for entry in self._entries if entry.kind == kind]

    def add_selection(self, selection: HardwareComponentSelection) -> None:
        self._selections.append(selection)

    def find_selections(self, kind: HardwareComponentKind) -> List[HardwareComponentSelection]:
        return [selection for selection in self._selections if selection.kind == kind]
