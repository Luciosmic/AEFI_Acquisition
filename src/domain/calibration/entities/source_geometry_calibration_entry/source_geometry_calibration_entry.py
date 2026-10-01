"""
Source Geometry Calibration Entry Entity

Responsibility:
- Immutable, append-only record of a caliper-measured 4-sphere source
  geometry (diameters + extremity-to-extremity distances), each value
  carrying its GUM expanded uncertainty.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Tuple
from uuid import UUID, uuid4

from domain.calibration.value_objects.caliper_measurement.caliper_measurement import CaliperMeasurement
from domain.calibration.value_objects.geometric_configuration_signature.geometric_configuration_signature import (
    GeometricConfigurationSignature,
)

# Index i -> the two sphere indices (into sphere_diameters, 0-based S1..S4)
# whose radii must be subtracted from pairwise_distances_ext[i] to get a
# positive center-to-center distance. Order matches GeometricConfigurationSignature
# / aefi_device_config.json: D_S1_S2, D_S3_S4, D_S1_S3, D_S1_S4, D_S2_S3, D_S2_S4.
_DISTANCE_SPHERE_PAIRS = ((0, 1), (2, 3), (0, 2), (0, 3), (1, 2), (1, 3))


@dataclass(frozen=True)
class SourceGeometryCalibrationEntry:
    """
    One append-only registry entry: the caliper-measured source geometry
    recorded at a specific time.

    Entity — identity is `entry_id`, not the values it carries. Immutable
    once created (the registry is constructive: entries are added, never
    edited or removed).
    """

    entry_id: UUID
    sphere_diameters: Tuple[CaliperMeasurement, CaliperMeasurement, CaliperMeasurement, CaliperMeasurement]
    pairwise_distances_ext: Tuple[
        CaliperMeasurement, CaliperMeasurement, CaliperMeasurement,
        CaliperMeasurement, CaliperMeasurement, CaliperMeasurement,
    ]
    recorded_at: datetime

    def __post_init__(self):
        if len(self.sphere_diameters) != 4:
            raise ValueError("sphere_diameters must carry exactly 4 measurements (S1..S4)")
        if len(self.pairwise_distances_ext) != 6:
            raise ValueError("pairwise_distances_ext must carry exactly 6 measurements")

        radii = [diameter.value_m / 2 for diameter in self.sphere_diameters]
        for distance, (i, j) in zip(self.pairwise_distances_ext, _DISTANCE_SPHERE_PAIRS):
            center_to_center = distance.value_m - radii[i] - radii[j]
            if center_to_center <= 0:
                raise ValueError(
                    f"Measured distance {distance.value_m:.5f}m is not greater than the sum of "
                    f"the two sphere radii ({radii[i] + radii[j]:.5f}m) — spheres would overlap "
                    "given the measured diameters, this is a measurement error, not a valid geometry"
                )

    @staticmethod
    def single(
        sphere_diameters: Tuple[CaliperMeasurement, ...],
        pairwise_distances_ext: Tuple[CaliperMeasurement, ...],
    ) -> "SourceGeometryCalibrationEntry":
        """Mint a fresh entry wrapping a freshly measured source geometry."""
        return SourceGeometryCalibrationEntry(
            entry_id=uuid4(),
            sphere_diameters=sphere_diameters,
            pairwise_distances_ext=pairwise_distances_ext,
            recorded_at=datetime.now(timezone.utc),
        )

    @property
    def geometric_configuration(self) -> GeometricConfigurationSignature:
        """Raw values only, dropping uncertainty — the equality-comparable
        signature consumed to tag sensor calibration entries."""
        return GeometricConfigurationSignature(
            sphere_diameters_m=tuple(m.value_m for m in self.sphere_diameters),
            pairwise_distances_ext_m=tuple(m.value_m for m in self.pairwise_distances_ext),
        )
