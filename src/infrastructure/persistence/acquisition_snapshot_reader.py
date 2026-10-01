"""
Acquisition Snapshot Reader

Responsibility:
- Implement `IAcquisitionSnapshotPort`: bundle the acquisition context into
  the per-scan metadata JSON —
  - `hardware_configuration`: built from the domain registries — for every
    hardware component kind, the mounted component and its current
    characterization; the latest sensor calibration and source geometry —
    plus the `warnings` of an incomplete / not characterized configuration;
  - the last-applied AD9106/motion configs and the probe connection
    defaults, still read from their on-disk JSON files.

Rationale:
- The hardware description in an export must be what the system knows
  (domain), not a copy of a hand-edited template: the metadata JSON is an
  output of the system, its schema is the domain model's.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from domain.calibration.calibration import Calibration
from domain.calibration.repositories.i_hardware_component_repository import IHardwareComponentRepository
from domain.calibration.repositories.i_sensor_calibration_repository import ISensorCalibrationRepository
from domain.calibration.repositories.i_source_geometry_calibration_repository import (
    ISourceGeometryCalibrationRepository,
)
from domain.calibration.value_objects.hardware_component_kind.hardware_component_kind import (
    HardwareComponentKind,
)

logger = logging.getLogger(__name__)


def _load_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Could not load acquisition snapshot source %s: %s", path, exc)
        return None


def _latest(entries):
    return max(entries, key=lambda entry: entry.recorded_at) if entries else None


class AcquisitionSnapshotReader:
    """Assembles the acquisition context available at scan start."""

    SOURCES = {
        "ad9106_last_config": Path(".aefi_acquisition/configs/ad9106_last_config.json"),
        "motion_last_config": Path(".aefi_acquisition/configs/motion_last_config.json"),
        "electric_field_probe_connection_defaults": Path("config_templates/electric_field_probe_config.json"),
    }

    def __init__(
        self,
        hardware_component_repository: IHardwareComponentRepository,
        sensor_calibration_repository: ISensorCalibrationRepository,
        source_geometry_calibration_repository: ISourceGeometryCalibrationRepository,
    ):
        self._hardware_component_repository = hardware_component_repository
        self._sensor_calibration_repository = sensor_calibration_repository
        self._source_geometry_calibration_repository = source_geometry_calibration_repository

    def read(self) -> Dict[str, Any]:
        snapshot: Dict[str, Any] = {"hardware_configuration": self._hardware_configuration()}
        for key, path in self.SOURCES.items():
            content = _load_json(path)
            if content is not None:
                snapshot[key] = content
        logger.info(
            "Acquisition snapshot assembled (hardware_configuration + %d/%d config files)",
            len(snapshot) - 1,
            len(self.SOURCES),
        )
        return snapshot

    def _hardware_configuration(self) -> Dict[str, Any]:
        warnings: List[str] = []
        configuration: Dict[str, Any] = {}

        for kind in HardwareComponentKind:
            name = Calibration.mounted_component_name(self._hardware_component_repository.find_selections(kind))
            entry = Calibration.current_characterization(self._hardware_component_repository.find_all(kind), name)
            if entry is None:
                configuration[kind.value] = None
                warnings.append(f"{kind.value}: nothing mounted — configuration incomplete")
                continue
            configuration[kind.value] = {
                "component_name": entry.component_name,
                "characterization": dict(entry.characterization.values),
                "units": {q.key: q.unit for q in kind.quantities},
                "entry_id": str(entry.entry_id),
                "recorded_at": entry.recorded_at.isoformat(),
            }
            for key in entry.characterization.uncharacterized():
                warnings.append(f"{kind.value} '{name}': {key} not characterized")

        sensor = _latest(self._sensor_calibration_repository.find_all())
        configuration["sensor_calibration_latest"] = asdict(sensor) if sensor else None
        if sensor is None:
            warnings.append("sensor_calibration: no sensor calibration recorded")

        geometry = _latest(self._source_geometry_calibration_repository.find_all())
        configuration["source_geometry_latest"] = asdict(geometry) if geometry else None
        if geometry is None:
            warnings.append("source_geometry: no source geometry recorded")

        configuration["warnings"] = warnings
        for warning in warnings:
            logger.warning("Acquisition snapshot: %s", warning)
        return configuration
