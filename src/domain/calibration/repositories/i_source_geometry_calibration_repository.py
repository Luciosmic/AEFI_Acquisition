from abc import ABC, abstractmethod
from typing import List

from domain.calibration.entities.source_geometry_calibration_entry.source_geometry_calibration_entry import (
    SourceGeometryCalibrationEntry,
)


class ISourceGeometryCalibrationRepository(ABC):
    """
    Interface for persisting the source geometry calibration registry
    (append-only entries). Follows the DDD Repository pattern.
    """

    @abstractmethod
    def add(self, entry: SourceGeometryCalibrationEntry) -> None:
        """
        Append a new calibration entry to the registry.

        The registry is constructive: this must never overwrite or remove
        an existing entry — it is a pure append.

        Args:
            entry: The calibration entry to add.
        """
        pass

    @abstractmethod
    def find_all(self) -> List[SourceGeometryCalibrationEntry]:
        """
        Retrieve every recorded calibration entry, in stored order.

        No filter at the repository level — there is a single source bench
        (unlike sensor calibration, no hardware-signature dimension
        applies here). Callers pick the most recent entry themselves
        (`SourceGeometryCalibrationService`), and this same method doubles
        as the "is the registry empty yet?" check used by the composition
        root to decide whether to seed from the legacy device config JSON.

        Returns:
            List of every SourceGeometryCalibrationEntry (empty if none
            recorded yet).
        """
        pass
