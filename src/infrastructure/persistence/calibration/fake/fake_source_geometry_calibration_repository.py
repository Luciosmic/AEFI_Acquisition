"""
Fake Source Geometry Calibration Repository

Responsibility:
- Implement `ISourceGeometryCalibrationRepository` purely in memory (list),
  for application-layer tests that must not depend on file I/O.

Rationale:
- Fake-over-Mock: application tests verify state (entries recorded) rather
  than interactions.
"""

from __future__ import annotations

from typing import List

from domain.calibration.entities.source_geometry_calibration_entry.source_geometry_calibration_entry import (
    SourceGeometryCalibrationEntry,
)
from domain.calibration.repositories.i_source_geometry_calibration_repository import (
    ISourceGeometryCalibrationRepository,
)


class FakeSourceGeometryCalibrationRepository(ISourceGeometryCalibrationRepository):
    """In-memory, append-only calibration registry for tests."""

    def __init__(self):
        self._entries: List[SourceGeometryCalibrationEntry] = []

    def add(self, entry: SourceGeometryCalibrationEntry) -> None:
        self._entries.append(entry)

    def find_all(self) -> List[SourceGeometryCalibrationEntry]:
        return list(self._entries)
