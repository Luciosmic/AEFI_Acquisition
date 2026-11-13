from abc import ABC, abstractmethod
from typing import List

from domain.test_bench_calibration.entities.mechanical_transmission_calibration_entry.mechanical_transmission_calibration_entry import (
    MechanicalTransmissionCalibrationEntry,
)


class IMechanicalTransmissionCalibrationRepository(ABC):
    """
    Interface for persisting the mechanical transmission registry
    (append-only entries). Follows the DDD Repository pattern.

    Responsibility:
        - `add(entry)`: append an entry — never overwrite or remove one.
        - `find_all()`: every entry, in stored order. The caller picks the current
          one (`Calibration.current_mechanical_transmission`); an empty result is
          also the composition root's "seed it from the template?" check.

    Rationale:
        Defines the persistence contract for the mechanical transmission registry,
        same Repository pattern as the source geometry registry: the domain declares
        WHAT to persist (an append-only registry of entries), infrastructure decides
        HOW (a JSON file, see `RealMechanicalTransmissionCalibrationRepository`).

    Design:
        - ABC in `domain/test_bench_calibration/repositories/`; implemented by
          `RealMechanicalTransmissionCalibrationRepository` (JSON,
          `.aefi_acquisition/calibrations/mechanical_transmission_calibration.json`)
          and `FakeMechanicalTransmissionCalibrationRepository` (in-memory), both in
          `infrastructure/persistence/calibration/`.
    """

    @abstractmethod
    def add(self, entry: MechanicalTransmissionCalibrationEntry) -> None:
        """Append a new entry — never overwrite or remove an existing one."""

    @abstractmethod
    def find_all(self) -> List[MechanicalTransmissionCalibrationEntry]:
        """Every recorded entry, in stored order (empty if none yet)."""
