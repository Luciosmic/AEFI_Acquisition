from abc import ABC, abstractmethod
from typing import List

from domain.calibration.entities.hardware_component_characterization_entry.hardware_component_characterization_entry import (
    HardwareComponentCharacterizationEntry,
)
from domain.calibration.entities.hardware_component_selection.hardware_component_selection import (
    HardwareComponentSelection,
)
from domain.calibration.value_objects.hardware_component_kind.hardware_component_kind import (
    HardwareComponentKind,
)


class IHardwareComponentRepository(ABC):
    """
    Persistence contract for the hardware component catalog (append-only
    characterization entries) and mounting log (append-only selections),
    per component kind. Follows the DDD Repository pattern.
    """

    @abstractmethod
    def add(self, entry: HardwareComponentCharacterizationEntry) -> None:
        """Append a characterization entry — never overwrite or remove one."""

    @abstractmethod
    def find_all(self, kind: HardwareComponentKind) -> List[HardwareComponentCharacterizationEntry]:
        """Every characterization entry of that kind, in recording order."""

    @abstractmethod
    def add_selection(self, selection: HardwareComponentSelection) -> None:
        """Append a "this component is mounted" record — never overwrite or remove one."""

    @abstractmethod
    def find_selections(self, kind: HardwareComponentKind) -> List[HardwareComponentSelection]:
        """The mounting log of that kind, in recording order."""
