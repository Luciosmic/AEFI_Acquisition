from abc import ABC, abstractmethod
from typing import List

from domain.test_bench.calibration.entities.hardware_component_characterization_entry.hardware_component_characterization_entry import (
    HardwareComponentCharacterizationEntry,
)
from domain.test_bench.calibration.entities.hardware_component_selection.hardware_component_selection import (
    HardwareComponentSelection,
)
from domain.test_bench.calibration.value_objects.hardware_component_kind.hardware_component_kind import (
    HardwareComponentKind,
)


class IHardwareComponentRepository(ABC):
    """
    Persistence contract for the hardware component catalog (append-only
    characterization entries) and mounting log (append-only selections),
    per component kind. Follows the DDD Repository pattern.

    Responsibility:
        - `add(entry)` / `find_all(kind)`: the catalog of characterizations. Entries
          sharing a name are that component's history; the latest is current.
        - `add_selection(selection)` / `find_selections(kind)`: the mounting log;
          the latest selection is the mounted component.

    Rationale:
        Without a domain contract the service would read and write files itself and
        could not be tested without a filesystem; the contract also pins the
        append-only promise of both logs (characterizations, mountings) in one place.

    Design:
        - One contract for every `HardwareComponentKind`.
        - Real: `infrastructure/persistence/calibration/real_hardware_component_repository.py`
          (one JSON file per kind in `.aefi_acquisition/calibrations/`).
        - Fake: `infrastructure/persistence/calibration/fake/fake_hardware_component_repository.py`.
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
