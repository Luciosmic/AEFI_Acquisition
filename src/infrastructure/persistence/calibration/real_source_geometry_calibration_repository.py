"""
Real Source Geometry Calibration Repository

Responsibility:
- Implement `ISourceGeometryCalibrationRepository` against a single plain
  JSON file: `{"entries": [...]}`.

Rationale:
- The calibration registry is decided to be append-only / constructive:
  `add()` must never overwrite or drop an existing entry. Plain JSON
  (no ORM) matches this codebase's existing config persistence style, and
  mirrors `RealSensorCalibrationRepository`.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

from domain.calibration.entities.source_geometry_calibration_entry.source_geometry_calibration_entry import (
    SourceGeometryCalibrationEntry,
)
from domain.calibration.repositories.i_source_geometry_calibration_repository import (
    ISourceGeometryCalibrationRepository,
)
from domain.calibration.value_objects.caliper_measurement.caliper_measurement import CaliperMeasurement

logger = logging.getLogger(__name__)


class RealSourceGeometryCalibrationRepository(ISourceGeometryCalibrationRepository):
    """JSON-file-backed, append-only calibration registry."""

    DEFAULT_PATH = Path(".aefi_acquisition/calibrations/source_geometry_calibration.json")

    def __init__(self, storage_path: Optional[Path] = None):
        self._storage_path = storage_path or self.DEFAULT_PATH

    def add(self, entry: SourceGeometryCalibrationEntry) -> None:
        data = self._load()
        data["entries"].append(self._serialize_entry(entry))
        self._write(data)
        logger.info("Saved source geometry calibration entry %s", entry.entry_id)

    def find_all(self) -> List[SourceGeometryCalibrationEntry]:
        data = self._load()
        entries = [self._deserialize_entry(raw) for raw in data["entries"]]
        logger.info("Found %d source geometry calibration entries", len(entries))
        return entries

    def _load(self) -> Dict[str, Any]:
        if not self._storage_path.exists():
            return {"entries": []}
        try:
            with self._storage_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            logger.error("Failed to load source geometry calibration registry %s: %s", self._storage_path, exc)
            return {"entries": []}
        data.setdefault("entries", [])
        return data

    def _write(self, data: Dict[str, Any]) -> None:
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        with self._storage_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    @staticmethod
    def _serialize_measurement(measurement: CaliperMeasurement) -> Dict[str, Any]:
        return {
            "value_m": measurement.value_m,
            "uncertainty_expanded_m": measurement.uncertainty_expanded_m,
            "k": measurement.k,
        }

    @staticmethod
    def _deserialize_measurement(raw: Dict[str, Any]) -> CaliperMeasurement:
        return CaliperMeasurement(
            value_m=raw["value_m"], uncertainty_expanded_m=raw["uncertainty_expanded_m"], k=raw["k"]
        )

    @classmethod
    def _serialize_entry(cls, entry: SourceGeometryCalibrationEntry) -> Dict[str, Any]:
        return {
            "entry_id": str(entry.entry_id),
            "sphere_diameters": [cls._serialize_measurement(m) for m in entry.sphere_diameters],
            "pairwise_distances_ext": [cls._serialize_measurement(m) for m in entry.pairwise_distances_ext],
            "recorded_at": entry.recorded_at.isoformat(),
        }

    @classmethod
    def _deserialize_entry(cls, raw: Dict[str, Any]) -> SourceGeometryCalibrationEntry:
        return SourceGeometryCalibrationEntry(
            entry_id=UUID(raw["entry_id"]),
            sphere_diameters=tuple(cls._deserialize_measurement(m) for m in raw["sphere_diameters"]),
            pairwise_distances_ext=tuple(
                cls._deserialize_measurement(m) for m in raw["pairwise_distances_ext"]
            ),
            recorded_at=datetime.fromisoformat(raw["recorded_at"]),
        )
