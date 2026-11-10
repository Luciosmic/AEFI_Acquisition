"""
Fake Mechanical Transmission Calibration Repository

Responsibility:
- Implement `IMechanicalTransmissionCalibrationRepository` purely in memory,
  for application-layer tests.
"""

from __future__ import annotations

from typing import List

from domain.test_bench.calibration.entities.mechanical_transmission_calibration_entry.mechanical_transmission_calibration_entry import (
    MechanicalTransmissionCalibrationEntry,
)
from domain.test_bench.calibration.repositories.i_mechanical_transmission_calibration_repository import (
    IMechanicalTransmissionCalibrationRepository,
)


class FakeMechanicalTransmissionCalibrationRepository(IMechanicalTransmissionCalibrationRepository):
    """In-memory, append-only mechanical transmission registry for tests."""

    def __init__(self):
        self._entries: List[MechanicalTransmissionCalibrationEntry] = []

    def add(self, entry: MechanicalTransmissionCalibrationEntry) -> None:
        self._entries.append(entry)

    def find_all(self) -> List[MechanicalTransmissionCalibrationEntry]:
        return list(self._entries)
