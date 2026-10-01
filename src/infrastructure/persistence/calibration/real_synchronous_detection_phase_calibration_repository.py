"""
Real Synchronous Detection Phase Calibration Repository

Responsibility:
- Implement `ISynchronousDetectionPhaseCalibrationRepository` against a
  single plain JSON file: `{"entries": [...], "compensation_enabled": bool}`.

Rationale:
- The calibration registry is decided to be append-only / constructive:
  `add()` must never overwrite or drop an existing entry. Plain JSON
  (no ORM) matches this codebase's existing config persistence style.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

from domain.calibration.entities.synchronous_detection_phase_calibration_entry.synchronous_detection_phase_calibration_entry import (
    SynchronousDetectionPhaseCalibrationEntry,
)
from domain.calibration.repositories.i_synchronous_detection_phase_calibration_repository import (
    ISynchronousDetectionPhaseCalibrationRepository,
)
from domain.calibration.value_objects.hardware_signature.hardware_signature import HardwareSignature
from infrastructure.persistence.calibration.hardware_signature_json import (
    hardware_signature_from_json,
    hardware_signature_to_json,
)
from domain.calibration.value_objects.synchronous_detection_phase_calibration_point.synchronous_detection_phase_calibration_point import (
    SynchronousDetectionPhaseCalibrationPoint,
)

_EMPTY_STORAGE: Dict[str, Any] = {"entries": [], "compensation_enabled": False}

logger = logging.getLogger(__name__)


class RealSynchronousDetectionPhaseCalibrationRepository(ISynchronousDetectionPhaseCalibrationRepository):
    """JSON-file-backed, append-only calibration registry."""

    DEFAULT_PATH = Path(".aefi_acquisition/calibrations/synchronous_detection_phase_calibration.json")

    def __init__(self, storage_path: Optional[Path] = None):
        self._storage_path = storage_path or self.DEFAULT_PATH

    def add(self, entry: SynchronousDetectionPhaseCalibrationEntry) -> None:
        data = self._load()
        data["entries"].append(self._serialize_entry(entry))
        self._write(data)
        logger.info(
            "Saved synchronous detection phase calibration entry %s for signature %s",
            entry.entry_id,
            entry.hardware_signature,
        )

    def find_by_hardware_signature(self, signature: HardwareSignature) -> List[SynchronousDetectionPhaseCalibrationEntry]:
        data = self._load()
        entries = [self._deserialize_entry(raw) for raw in data["entries"]]
        matches = [entry for entry in entries if entry.hardware_signature == signature]
        logger.info(
            "Found %d calibration entries for hardware signature %s",
            len(matches),
            signature,
        )
        return matches

    def load_compensation_enabled(self) -> bool:
        data = self._load()
        return bool(data.get("compensation_enabled", False))

    def save_compensation_enabled(self, enabled: bool) -> None:
        data = self._load()
        data["compensation_enabled"] = enabled
        self._write(data)
        logger.info("Phase compensation enabled flag saved: %s", enabled)

    def _load(self) -> Dict[str, Any]:
        if not self._storage_path.exists():
            return {"entries": [], "compensation_enabled": False}
        try:
            with self._storage_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            logger.error("Failed to load calibration registry %s: %s", self._storage_path, exc)
            return {"entries": [], "compensation_enabled": False}
        data.setdefault("entries", [])
        data.setdefault("compensation_enabled", False)
        return data

    def _write(self, data: Dict[str, Any]) -> None:
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        with self._storage_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    @staticmethod
    def _serialize_entry(entry: SynchronousDetectionPhaseCalibrationEntry) -> Dict[str, Any]:
        return {
            "entry_id": str(entry.entry_id),
            "hardware_signature": hardware_signature_to_json(entry.hardware_signature),
            "points": [
                {"frequency_hz": point.frequency_hz, "delta_phi_degrees": point.delta_phi_degrees}
                for point in entry.points
            ],
            "recorded_at": entry.recorded_at.isoformat(),
        }

    @staticmethod
    def _deserialize_entry(raw: Dict[str, Any]) -> SynchronousDetectionPhaseCalibrationEntry:
        signature = hardware_signature_from_json(raw["hardware_signature"])
        points = tuple(
            SynchronousDetectionPhaseCalibrationPoint(
                frequency_hz=point_raw["frequency_hz"],
                delta_phi_degrees=point_raw["delta_phi_degrees"],
            )
            for point_raw in raw["points"]
        )
        return SynchronousDetectionPhaseCalibrationEntry(
            entry_id=UUID(raw["entry_id"]),
            hardware_signature=signature,
            points=points,
            recorded_at=datetime.fromisoformat(raw["recorded_at"]),
        )
