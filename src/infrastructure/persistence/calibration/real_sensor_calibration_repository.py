"""
Real Sensor Calibration Repository

Responsibility:
- Implement `ISensorCalibrationRepository` against a single plain JSON
  file: `{"entries": [...]}`.

Rationale:
- The calibration registry is decided to be append-only / constructive:
  `add()` must never overwrite or drop an existing entry. Plain JSON
  (no ORM) matches this codebase's existing config persistence style, and
  mirrors `RealSynchronousDetectionPhaseCalibrationRepository`.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

from domain.calibration.entities.sensor_calibration_entry.sensor_calibration_entry import (
    SensorCalibrationEntry,
)
from domain.calibration.repositories.i_sensor_calibration_repository import (
    ISensorCalibrationRepository,
)
from domain.calibration.value_objects.rotation_convention.rotation_convention import RotationConvention
from domain.calibration.value_objects.sensor_rotation_angles.sensor_rotation_angles import (
    SensorRotationAngles,
)

logger = logging.getLogger(__name__)


class RealSensorCalibrationRepository(ISensorCalibrationRepository):
    """JSON-file-backed, append-only calibration registry."""

    DEFAULT_PATH = Path(".aefi_acquisition/calibrations/sensor_calibration.json")

    def __init__(self, storage_path: Optional[Path] = None):
        self._storage_path = storage_path or self.DEFAULT_PATH

    def add(self, entry: SensorCalibrationEntry) -> None:
        data = self._load()
        data["entries"].append(self._serialize_entry(entry))
        self._write(data)
        logger.info(
            "Saved sensor calibration entry %s for sensor mounting %s",
            entry.entry_id,
            entry.sensor_mounting_id,
        )

    def find_all(self) -> List[SensorCalibrationEntry]:
        entries = self._readable_entries()
        logger.info("Found %d sensor calibration entries in total", len(entries))
        return entries

    def _readable_entries(self) -> List[SensorCalibrationEntry]:
        """One unreadable entry (e.g. stored under a rotation convention no
        longer supported) must not take the whole registry — and the
        application start — down with it: it is skipped, loudly."""
        entries = []
        for raw in self._load()["entries"]:
            try:
                entries.append(self._deserialize_entry(raw))
            except (KeyError, TypeError, ValueError) as exc:
                logger.error(
                    "Skipping unreadable sensor calibration entry %s in %s: %s: %s",
                    raw.get("entry_id"),
                    self._storage_path,
                    type(exc).__name__,
                    exc,
                )
        return entries

    def _load(self) -> Dict[str, Any]:
        if not self._storage_path.exists():
            return {"entries": []}
        try:
            with self._storage_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            logger.error("Failed to load sensor calibration registry %s: %s", self._storage_path, exc)
            return {"entries": []}
        data.setdefault("entries", [])
        return data

    def _write(self, data: Dict[str, Any]) -> None:
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        with self._storage_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    @staticmethod
    def _serialize_entry(entry: SensorCalibrationEntry) -> Dict[str, Any]:
        return {
            "entry_id": str(entry.entry_id),
            "sensor_mounting_id": str(entry.sensor_mounting_id),
            "source_geometry_entry_id": str(entry.source_geometry_entry_id),
            "angles": {
                "theta_x_degrees": entry.angles.theta_x_degrees,
                "theta_y_degrees": entry.angles.theta_y_degrees,
                "theta_z_degrees": entry.angles.theta_z_degrees,
                "convention": {
                    "type": entry.angles.convention.type,
                    "order": entry.angles.convention.order,
                    "direction": entry.angles.convention.direction,
                },
            },
            "recorded_at": entry.recorded_at.isoformat(),
        }

    @staticmethod
    def _deserialize_entry(raw: Dict[str, Any]) -> SensorCalibrationEntry:
        angles_raw = raw["angles"]
        angles = SensorRotationAngles(
            theta_x_degrees=angles_raw["theta_x_degrees"],
            theta_y_degrees=angles_raw["theta_y_degrees"],
            theta_z_degrees=angles_raw["theta_z_degrees"],
            convention=RotationConvention(**angles_raw["convention"]),
        )
        return SensorCalibrationEntry(
            entry_id=UUID(raw["entry_id"]),
            sensor_mounting_id=UUID(raw["sensor_mounting_id"]),
            source_geometry_entry_id=UUID(raw["source_geometry_entry_id"]),
            angles=angles,
            recorded_at=datetime.fromisoformat(raw["recorded_at"]),
        )
