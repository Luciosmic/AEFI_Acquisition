from abc import ABC, abstractmethod
from typing import List

from domain.calibration.entities.synchronous_detection_phase_calibration_entry.synchronous_detection_phase_calibration_entry import (
    SynchronousDetectionPhaseCalibrationEntry,
)
from domain.calibration.value_objects.hardware_signature.hardware_signature import HardwareSignature


class ISynchronousDetectionPhaseCalibrationRepository(ABC):
    """
    Interface for persisting the synchronous detection phase calibration
    registry (append-only entries) and the compensation-enabled flag.
    Follows the DDD Repository pattern.
    """

    @abstractmethod
    def add(self, entry: SynchronousDetectionPhaseCalibrationEntry) -> None:
        """
        Append a new calibration entry to the registry.

        The registry is constructive: this must never overwrite or remove
        an existing entry, regardless of hardware signature — it is a
        pure append.

        Args:
            entry: The calibration entry to add.
        """
        pass

    @abstractmethod
    def find_by_hardware_signature(
        self, signature: HardwareSignature
    ) -> List[SynchronousDetectionPhaseCalibrationEntry]:
        """
        Retrieve all calibration entries recorded for a given hardware
        signature.

        Args:
            signature: The hardware setup to filter entries by.

        Returns:
            List of matching SynchronousDetectionPhaseCalibrationEntry
            objects (empty if none recorded yet).
        """
        pass

    @abstractmethod
    def load_compensation_enabled(self) -> bool:
        """
        Read the persisted synchronous detection compensation flag.

        Returns:
            The persisted state, or False if none has been saved yet.
        """
        pass

    @abstractmethod
    def save_compensation_enabled(self, enabled: bool) -> None:
        """
        Persist the synchronous detection compensation flag.

        Args:
            enabled: The new state to persist.
        """
        pass
