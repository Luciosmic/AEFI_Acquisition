"""
Cube Sensor Field Simulator

See cube_sensor_field_simulator_intention.md.
"""

import json
import random
import sys
from pathlib import Path
from typing import Optional, Tuple

import numpy as np

from infrastructure.mocks.point_charge_field_simulator import PointChargeFieldSimulator

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_EXTERNAL_MODULES = _PROJECT_ROOT / "external_modules"
if str(_EXTERNAL_MODULES) not in sys.path:
    sys.path.insert(0, str(_EXTERNAL_MODULES))

from cube_visualizer.domain.sensor_rotation import rotation_from_euler_xyz  # noqa: E402

_DEFAULT_CONFIG_PATH = Path(".aefi_acquisition") / "configs" / "aefi_device_config.json"

# Realistic-noise defaults for from_default_config() (the real app's mock
# wiring). from_config() defaults both to 0.0 so tests stay deterministic.
_DEFAULT_SOURCE_LEVEL_NOISE_STD_PERCENT = 0.01  # DDS amplitude stability jitter
_DEFAULT_SENSOR_NOISE_STD_V = 0.00002  # sensor + conditioning electronics noise


class CubeSensorFieldSimulator:
    """
    Simulates the 8mm cube AEFI sensor, fixed at the exact center of the
    4-sphere square: each output axis is the finite-difference field between
    the spatial-average potential over that axis's two opposing cube faces.

    Models two distinct, independently-configurable noise sources — not the
    ADC's own quantization noise, which is negligible at this signal scale
    and belongs to FakeMCUSerialCommunicator instead:
    - Source (DDS) amplitude jitter: the driven level fluctuates slightly
      sample-to-sample; drawn once per compute_axis_voltages() call, so it's
      correlated across every face-grid point (same instant, same driven
      voltage), not resampled per point.
    - Sensor (+ conditioning electronics) read noise: independent Gaussian
      noise added per output axis, after the field computation.
    """

    FACE_GRID_POINTS = 5  # per side -> 25 samples/face, cell-center sampling

    def __init__(
        self,
        point_charge_simulator: PointChargeFieldSimulator,
        dimension_m: float,
        gain_v_per_v_per_m: float,
        rotation,
        source_level_noise_std_percent: float = 0.0,
        sensor_noise_std_v: float = 0.0,
        rng: Optional[random.Random] = None,
    ):
        self._spheres = point_charge_simulator
        self._dimension = dimension_m
        self._gain = gain_v_per_v_per_m
        self._rotation = rotation
        self._source_level_noise_std_percent = source_level_noise_std_percent
        self._sensor_noise_std_v = sensor_noise_std_v
        self._rng = rng if rng is not None else random.Random()
        self._face_offsets_1d = self._build_face_offsets()

    def _build_face_offsets(self) -> np.ndarray:
        half = self._dimension / 2.0
        n = self.FACE_GRID_POINTS
        step = self._dimension / n
        return -half + step / 2.0 + step * np.arange(n)

    @classmethod
    def from_config(
        cls,
        config: dict,
        point_charge_simulator: Optional[PointChargeFieldSimulator] = None,
        source_level_noise_std_percent: float = 0.0,
        sensor_noise_std_v: float = 0.0,
        rng: Optional[random.Random] = None,
    ) -> "CubeSensorFieldSimulator":
        sensor = config["sensor"]
        dimension = sensor["dimension"]["value"]
        gain = sensor["calibration"]["gain"]["value"]
        rot = sensor["calibration"]["sensor_to_lab_rotation"]
        rotation = rotation_from_euler_xyz(rot["theta_x"], rot["theta_y"], rot["theta_z"])

        spheres = point_charge_simulator or PointChargeFieldSimulator.from_config(config)
        return cls(
            spheres, dimension, gain, rotation,
            source_level_noise_std_percent=source_level_noise_std_percent,
            sensor_noise_std_v=sensor_noise_std_v,
            rng=rng,
        )

    @classmethod
    def from_default_config(cls, config_path: Path = _DEFAULT_CONFIG_PATH) -> "CubeSensorFieldSimulator":
        with open(config_path, encoding="utf-8") as f:
            return cls.from_config(
                json.load(f),
                source_level_noise_std_percent=_DEFAULT_SOURCE_LEVEL_NOISE_STD_PERCENT,
                sensor_noise_std_v=_DEFAULT_SENSOR_NOISE_STD_V,
            )

    def compute_axis_voltages(self, level_s1_s2_percent: float, level_s3_s4_percent: float) -> Tuple[float, float, float]:
        """Simulated (in-phase) sensor voltage per axis (x, y, z), sensor frame."""
        # Source jitter: one draw per call, shared by every face-grid sample
        # below — it's the same instantaneous driven voltage everywhere.
        if self._source_level_noise_std_percent:
            level_s1_s2_percent += self._rng.gauss(0.0, self._source_level_noise_std_percent)
            level_s3_s4_percent += self._rng.gauss(0.0, self._source_level_noise_std_percent)

        voltages = []
        for axis in range(3):
            v_pos = self._face_average_potential(axis, +1.0, level_s1_s2_percent, level_s3_s4_percent)
            v_neg = self._face_average_potential(axis, -1.0, level_s1_s2_percent, level_s3_s4_percent)
            field = (v_neg - v_pos) / self._dimension
            u = field / self._gain
            if self._sensor_noise_std_v:
                u += self._rng.gauss(0.0, self._sensor_noise_std_v)
            voltages.append(u)
        return tuple(voltages)

    def _face_average_potential(
        self, axis: int, sign: float, level_s1_s2_percent: float, level_s3_s4_percent: float
    ) -> float:
        other_axes = [i for i in range(3) if i != axis]
        half = self._dimension / 2.0

        total = 0.0
        count = 0
        for u in self._face_offsets_1d:
            for v in self._face_offsets_1d:
                local = np.zeros(3)
                local[axis] = sign * half
                local[other_axes[0]] = u
                local[other_axes[1]] = v
                world_point = self._rotation.apply(local)  # sensor center fixed at origin
                total += self._spheres.potential_at(world_point, level_s1_s2_percent, level_s3_s4_percent)
                count += 1
        return total / count
