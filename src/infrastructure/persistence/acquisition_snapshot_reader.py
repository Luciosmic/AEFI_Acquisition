"""
Acquisition Snapshot Reader

Responsibility:
- Implement `IAcquisitionSnapshotPort`: bundle the acquisition context into
  the per-scan metadata JSON —
  - `hardware_configuration`: built from the domain registries — for every
    hardware component kind, the mounted component and its current
    characterization; the latest sensor calibration and source geometry,
    with the sphere positions reconstructed from it (`source_frame_reconstruction`)
    — plus the `warnings` of an incomplete / not characterized configuration;
  - `hardware_settings`: the settings applied to the AD9106, ADS131A04 and
    MCU (default + last resolved) — n_avg, ADC oversampling, clock dividers,
    gains, Vref, DDS gains/phases/frequency. Without them an export cannot be
    reproduced: n_avg and the oversampling set both the noise and the rate;
  - the last motion config and the probe connection defaults, still read
    from their on-disk JSON files.

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
from domain.calibration.entities.source_geometry_calibration_entry.source_geometry_calibration_entry import (
    SourceGeometryCalibrationEntry,
)
from domain.calibration.errors.source_geometry_inconsistent_error import SourceGeometryInconsistentError
from domain.calibration.services.source_frame_solver.source_frame_solver import SourceFrameSolver
from domain.calibration.repositories.i_hardware_component_repository import IHardwareComponentRepository
from domain.calibration.repositories.i_sensor_calibration_repository import ISensorCalibrationRepository
from domain.calibration.repositories.i_source_geometry_calibration_repository import (
    ISourceGeometryCalibrationRepository,
)
from domain.calibration.value_objects.hardware_component_kind.hardware_component_kind import (
    HardwareComponentKind,
)
from infrastructure.hardware.micro_controller.hardware_config_resolution import resolve_config

logger = logging.getLogger(__name__)

HARDWARE_CONFIGS_DIR = Path(".aefi_acquisition/configs")
HARDWARE_SETTINGS_CHIPS = ("ad9106", "ads131a04", "mcu")


def _load_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Could not load acquisition snapshot source %s: %s", path, exc)
        return None


def _latest(entries):
    return max(entries, key=lambda entry: entry.recorded_at) if entries else None


def _source_frame_reconstruction(entry: SourceGeometryCalibrationEntry) -> Dict[str, Any]:
    """Sphere centers reconstructed from `entry`, keyed S1..S4 / D_Si_Sj."""
    frame = SourceFrameSolver.solve(entry)
    spheres = ("S1", "S2", "S3", "S4")
    distances = [f"D_S{i + 1}_S{j + 1}" for i, j in entry.center_to_center_distances_m]
    return {
        "source_geometry_entry_id": str(entry.entry_id),
        "frame": (
            "origin = centroid of the 4 sphere centers, +x/+y along the sides of the best-fit square, z=0 "
            "(coplanar by construction); S1=x_neg_y_pos, S2=x_pos_y_neg, S3=x_pos_y_pos, S4=x_neg_y_neg"
        ),
        "unit": "m",
        "sphere_positions": dict(zip(spheres, frame.sphere_positions_m)),
        "sphere_radii": dict(zip(spheres, frame.sphere_radii_m)),
        "best_fit_square": {
            "side": frame.best_fit_square_side_m,
            "positions": dict(zip(spheres, frame.best_fit_square_positions_m)),
            "residuals": dict(zip(spheres, frame.square_residuals_m)),
            "rms_residual": frame.square_rms_residual_m,
        },
        "distance_residuals": dict(zip(distances, frame.distance_residuals_m)),
    }


class AcquisitionSnapshotReader:
    """Assembles the acquisition context available at scan start."""

    SOURCES = {
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
        snapshot: Dict[str, Any] = {
            "hardware_configuration": self._hardware_configuration(),
            "hardware_settings": self._hardware_settings(),
        }
        for key, path in self.SOURCES.items():
            content = _load_json(path)
            if content is not None:
                snapshot[key] = content
        logger.info(
            "Acquisition snapshot assembled (hardware_configuration + hardware_settings + %d/%d config files)",
            len(snapshot) - 2,
            len(self.SOURCES),
        )
        return snapshot

    def _hardware_settings(self) -> Dict[str, Any]:
        """Settings applied to each configurable chip at scan start: default +
        last config resolved exactly as the hardware composition root and the
        configurators do (resolve_config, last wins) — n_avg (MCU averaging),
        ADC oversampling / clock dividers / gains / Vref, DDS gains/phases/frequency.
        ponytail: synchronous-detection compensation writes DDS phases without
        persisting them, so `ad9106` shows the uncompensated phases while it is on."""
        settings: Dict[str, Any] = {
            "source": "resolved <chip>_default_config.json + <chip>_last_config.json (last wins)",
        }
        warnings: List[str] = []
        for chip in HARDWARE_SETTINGS_CHIPS:
            layers = []
            for layer in ("default", "last"):
                path = HARDWARE_CONFIGS_DIR / f"{chip}_{layer}_config.json"
                content = _load_json(path) if path.exists() else {}
                if content is None:
                    warnings.append(f"{chip}: {path.name} unreadable — applied settings may differ")
                    content = {}
                layers.append(content)
            resolved = resolve_config(*layers)
            settings[chip] = resolved or None
            if not resolved:
                warnings.append(f"{chip}: no config file — applied settings unknown")
        settings["warnings"] = warnings
        for warning in warnings:
            logger.warning("Acquisition snapshot: %s", warning)
        return settings

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
        configuration["source_frame_reconstruction"] = None
        if geometry is None:
            warnings.append("source_geometry: no source geometry recorded")
        else:
            try:
                configuration["source_frame_reconstruction"] = _source_frame_reconstruction(geometry)
            except SourceGeometryInconsistentError as e:
                warnings.append(f"source_frame_reconstruction: latest source geometry cannot be reconstructed ({e})")

        configuration["warnings"] = warnings
        for warning in warnings:
            logger.warning("Acquisition snapshot: %s", warning)
        return configuration
