"""
Fake Synchronous Detection Phase Calibration Repository

Responsibility:
- Implement `ISynchronousDetectionPhaseCalibrationRepository` purely in
  memory (list + bool), for application-layer tests that must not depend
  on file I/O.

Rationale:
- Fake-over-Mock: application tests verify state (entries recorded,
  compensation flag persisted) rather than interactions.
"""

from __future__ import annotations

from typing import List

from domain.calibration.entities.synchronous_detection_phase_calibration_entry.synchronous_detection_phase_calibration_entry import (
    SynchronousDetectionPhaseCalibrationEntry,
)
from domain.calibration.repositories.i_synchronous_detection_phase_calibration_repository import (
    ISynchronousDetectionPhaseCalibrationRepository,
)
from domain.calibration.value_objects.hardware_signature.hardware_signature import HardwareSignature


class FakeSynchronousDetectionPhaseCalibrationRepository(ISynchronousDetectionPhaseCalibrationRepository):
    """In-memory, append-only calibration registry for tests."""

    def __init__(self):
        self._entries: List[SynchronousDetectionPhaseCalibrationEntry] = []
        self._compensation_enabled: bool = False

    def add(self, entry: SynchronousDetectionPhaseCalibrationEntry) -> None:
        self._entries.append(entry)

    def find_by_hardware_signature(self, signature: HardwareSignature) -> List[SynchronousDetectionPhaseCalibrationEntry]:
        return [entry for entry in self._entries if entry.hardware_signature == signature]

    def load_compensation_enabled(self) -> bool:
        return self._compensation_enabled

    def save_compensation_enabled(self, enabled: bool) -> None:
        self._compensation_enabled = enabled
