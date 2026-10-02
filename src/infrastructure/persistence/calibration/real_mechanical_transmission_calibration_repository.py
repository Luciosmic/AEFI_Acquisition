"""
Real Mechanical Transmission Calibration Repository

Responsibility:
- Implement `IMechanicalTransmissionCalibrationRepository` against a single
  plain JSON file: `{"entries": [...]}` (append-only).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

from domain.calibration.entities.mechanical_transmission_calibration_entry.mechanical_transmission_calibration_entry import (
    MechanicalTransmissionCalibrationEntry,
)
from domain.calibration.repositories.i_mechanical_transmission_calibration_repository import (
    IMechanicalTransmissionCalibrationRepository,
)

logger = logging.getLogger(__name__)


class RealMechanicalTransmissionCalibrationRepository(IMechanicalTransmissionCalibrationRepository):
    """JSON-file-backed, append-only mechanical transmission registry."""

    DEFAULT_PATH = Path(".aefi_acquisition/calibrations/mechanical_transmission_calibration.json")

    def __init__(self, storage_path: Optional[Path] = None):
        self._storage_path = storage_path or self.DEFAULT_PATH

    def add(self, entry: MechanicalTransmissionCalibrationEntry) -> None:
        data = self._load()
        data["entries"].append(self._serialize_entry(entry))
        self._write(data)
        logger.info("Saved mechanical transmission calibration entry %s", entry.entry_id)

    def find_all(self) -> List[MechanicalTransmissionCalibrationEntry]:
        entries = [self._deserialize_entry(raw) for raw in self._load()["entries"]]
        logger.info("Found %d mechanical transmission calibration entries", len(entries))
        return entries

    def _load(self) -> Dict[str, Any]:
        if not self._storage_path.exists():
            return {"entries": []}
        try:
            with self._storage_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            logger.error("Failed to load mechanical transmission registry %s: %s", self._storage_path, exc)
            return {"entries": []}
        data.setdefault("entries", [])
        return data

    def _write(self, data: Dict[str, Any]) -> None:
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        with self._storage_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    @staticmethod
    def _serialize_entry(entry: MechanicalTransmissionCalibrationEntry) -> Dict[str, Any]:
        return {
            "entry_id": str(entry.entry_id),
            "motor_mounting_id": str(entry.motor_mounting_id),
            "stepper_driver_mounting_id": str(entry.stepper_driver_mounting_id),
            "microsteps": entry.microsteps,
            "driver_current_a": entry.driver_current_a,
            "driver_peak_current_a": entry.driver_peak_current_a,
            "travel_per_motor_revolution_mm": entry.travel_per_motor_revolution_mm,
            "recorded_at": entry.recorded_at.isoformat(),
        }

    @staticmethod
    def _deserialize_entry(raw: Dict[str, Any]) -> MechanicalTransmissionCalibrationEntry:
        return MechanicalTransmissionCalibrationEntry(
            entry_id=UUID(raw["entry_id"]),
            motor_mounting_id=UUID(raw["motor_mounting_id"]),
            stepper_driver_mounting_id=UUID(raw["stepper_driver_mounting_id"]),
            microsteps=int(raw["microsteps"]),
            driver_current_a=float(raw["driver_current_a"]),
            driver_peak_current_a=float(raw["driver_peak_current_a"]),
            travel_per_motor_revolution_mm=float(raw["travel_per_motor_revolution_mm"]),
            recorded_at=datetime.fromisoformat(raw["recorded_at"]),
        )
