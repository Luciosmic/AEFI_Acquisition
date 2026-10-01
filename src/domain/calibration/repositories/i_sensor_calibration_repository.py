from abc import ABC, abstractmethod
from typing import List

from domain.calibration.entities.sensor_calibration_entry.sensor_calibration_entry import (
    SensorCalibrationEntry,
)


class ISensorCalibrationRepository(ABC):
    """
    Interface for persisting the sensor calibration registry
    (append-only entries). Follows the DDD Repository pattern.
    """

    @abstractmethod
    def add(self, entry: SensorCalibrationEntry) -> None:
        """
        Append a new calibration entry to the registry.

        The registry is constructive: this must never overwrite or remove
        an existing entry, regardless of hardware signature or geometric
        configuration — it is a pure append.

        Args:
            entry: The calibration entry to add.
        """
        pass

    @abstractmethod
    def find_all(self) -> List[SensorCalibrationEntry]:
        """
        Retrieve every entry ever recorded, all sensor mountings and source
        geometries included — `SensorCalibrationService` selects those of the
        current mounting and geometry.
        """
        pass
