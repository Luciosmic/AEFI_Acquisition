"""
Ideal Sensor Rotation Reader

Responsibility:
- Read the ideal (nominal) mounting angles of the rotation P (brings the
  sensor from the sources frame to its current mounting) from
  `config_templates/aefi_device_config.json`
  (`sensor.calibration.sources_to_sensor_rotation`, angles + convention)
  and map it onto the domain `SensorRotationAngles` VO.

Rationale:
- These mounting angles are the default rotation applied when no sensor calibration
  exists for the current source geometry. Unlike the other config readers,
  a missing value is an error, not a silent 0: a wrong rotation would
  corrupt every measured field without any visible failure.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from domain.calibration.value_objects.rotation_convention.rotation_convention import RotationConvention
from domain.calibration.value_objects.sensor_rotation_angles.sensor_rotation_angles import (
    SensorRotationAngles,
)

logger = logging.getLogger(__name__)


class IdealSensorRotationReader:
    """Maps `sensor.calibration.sources_to_sensor_rotation` to `SensorRotationAngles`."""

    DEFAULT_PATH = Path("config_templates/aefi_device_config.json")

    def read(self, path: Optional[Path] = None) -> SensorRotationAngles:
        resolved_path = path or self.DEFAULT_PATH
        with resolved_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        try:
            rotation = data["sensor"]["calibration"]["sources_to_sensor_rotation"]
            convention_raw = rotation["convention"]
            angles = SensorRotationAngles(
                theta_x_degrees=float(rotation["theta_x"]),
                theta_y_degrees=float(rotation["theta_y"]),
                theta_z_degrees=float(rotation["theta_z"]),
                convention=RotationConvention(
                    type=convention_raw["type"],
                    order=convention_raw["order"],
                    direction=convention_raw["direction"],
                ),
            )
        except KeyError as exc:
            raise ValueError(
                f"{resolved_path}: sensor.calibration.sources_to_sensor_rotation is incomplete "
                f"(missing {exc}) — the ideal sensor rotation must be fully declared"
            ) from exc

        logger.info("Ideal sensor rotation read from %s: %s", resolved_path, angles)
        return angles
