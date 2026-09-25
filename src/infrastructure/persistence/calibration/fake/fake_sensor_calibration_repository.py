"""
Fake Sensor Calibration Repository

Responsibility:
- Implement `ISensorCalibrationRepository` purely in memory (list),
  for application-layer tests that must not depend on file I/O.

Rationale:
- Fake-over-Mock: application tests verify state (entries recorded) rather
  than interactions.
"""

from __future__ import annotations

from typing import List

from domain.calibration.entities.sensor_calibration_entry.sensor_calibration_entry import (
    SensorCalibrationEntry,
)
from domain.calibration.repositories.i_sensor_calibration_repository import (
    ISensorCalibrationRepository,
)


class FakeSensorCalibrationRepository(ISensorCalibrationRepository):
    """In-memory, append-only calibration registry for tests."""

    def __init__(self):
        self._entries: List[SensorCalibrationEntry] = []

    def add(self, entry: SensorCalibrationEntry) -> None:
        self._entries.append(entry)

    def find_all(self) -> List[SensorCalibrationEntry]:
        return list(self._entries)
