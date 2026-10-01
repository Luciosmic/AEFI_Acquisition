from abc import ABC, abstractmethod
from typing import List

from domain.calibration.entities.mechanical_transmission_calibration_entry.mechanical_transmission_calibration_entry import (
    MechanicalTransmissionCalibrationEntry,
)


class IMechanicalTransmissionCalibrationRepository(ABC):
    """
    Interface for persisting the mechanical transmission registry
    (append-only entries). Follows the DDD Repository pattern.
    """

    @abstractmethod
    def add(self, entry: MechanicalTransmissionCalibrationEntry) -> None:
        """Append a new entry — never overwrite or remove an existing one."""

    @abstractmethod
    def find_all(self) -> List[MechanicalTransmissionCalibrationEntry]:
        """Every recorded entry, in stored order (empty if none yet)."""
