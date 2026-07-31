"""
Point Charge Field Simulator

See point_charge_field_simulator_intention.md.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import numpy as np

from domain.shared_kernel.excitation.value_objects.sphere_id import SphereId

VOLTS_PER_PERCENT = 1.06  # 10% level = 10.6V RMS, linear to 100% = 106V RMS

_DEFAULT_CONFIG_PATH = Path(".aefi_acquisition") / "configs" / "aefi_device_config.json"


@dataclass(frozen=True)
class SpherePosition:
    """3D position (source frame, meters) and physical radius of one sphere."""
    position_m: np.ndarray
    radius_m: float


class PointChargeFieldSimulator:
    """
    The 4 excitation spheres' electrostatic potential, as the superposition
    of 4 charged-sphere sources: V(r) = V0 * R / r outside each sphere's
    surface. Pure geometry + physics — knows nothing about a sensor.
    """

    def __init__(self, sphere_positions: Dict[SphereId, SpherePosition]):
        self._geometry = sphere_positions

    @classmethod
    def from_config(cls, config: dict) -> "PointChargeFieldSimulator":
        """Build from an already-loaded aefi_device_config.json dict."""
        geo = config["excitation"]["sources_geometry"]
        diam = geo["sphere_diameters"]
        dist = geo["pairwise_distances_ext"]

        radii = {s: diam[s.name]["value"] / 2 for s in SphereId}
        # S1<->S2 and S3<->S4 are the square's two diagonals — perfect-square
        # simplification: sensor at exact center, so center_distance = half
        # the (averaged) diagonal, same for all 4 spheres.
        d_12 = dist["D_S1_S2"]["value"] - radii[SphereId.S1] - radii[SphereId.S2]
        d_34 = dist["D_S3_S4"]["value"] - radii[SphereId.S3] - radii[SphereId.S4]
        r_center = (d_12 + d_34) / 4.0
        sqrt2 = np.sqrt(2.0)

        sphere_positions = {}
        for s in SphereId:
            x_sign = 1.0 if s.x_sign == "pos" else -1.0
            y_sign = 1.0 if s.y_sign == "pos" else -1.0
            position = r_center * np.array([x_sign, y_sign, 0.0]) / sqrt2
            sphere_positions[s] = SpherePosition(position_m=position, radius_m=radii[s])

        return cls(sphere_positions)

    @classmethod
    def from_default_config(cls, config_path: Path = _DEFAULT_CONFIG_PATH) -> "PointChargeFieldSimulator":
        with open(config_path, encoding="utf-8") as f:
            return cls.from_config(json.load(f))

    def potential_at(self, point: np.ndarray, level_s1_s2_percent: float, level_s3_s4_percent: float) -> float:
        """Electrostatic potential (V) at an arbitrary source-frame point."""
        total = 0.0
        for sphere in SphereId:
            level = level_s1_s2_percent if sphere in (SphereId.S1, SphereId.S2) else level_s3_s4_percent
            sign = 1.0 if sphere.is_direct_output else -1.0
            v0 = sign * level * VOLTS_PER_PERCENT

            g = self._geometry[sphere]
            r = np.linalg.norm(point - g.position_m)
            total += v0 * g.radius_m / r
        return total
