"""
Geometric Configuration Signature Value Object

Responsibility:
- Identify the physical sphere-mounting geometry (caliper measurements) a
  calibration entry was recorded against.
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class GeometricConfigurationSignature:
    """
    Immutable snapshot of the raw caliper measurements that define the
    4-sphere source geometry, read from
    `config_templates/aefi_device_config.json` (`excitation.sources_geometry`)
    by `GeometricConfigurationReader` (infrastructure) — this VO itself has
    no knowledge of that file.

    Two entries recorded against the same physical mounting compare equal;
    any re-measurement (new caliper pass after reassembly) changes at least
    one value and therefore the signature.
    """

    sphere_diameters_m: Tuple[float, float, float, float]  # S1, S2, S3, S4
    pairwise_distances_ext_m: Tuple[float, float, float, float, float, float]
    # D_S1_S2, D_S3_S4, D_S1_S3, D_S1_S4, D_S2_S3, D_S2_S4

    def __post_init__(self):
        if len(self.sphere_diameters_m) != 4:
            raise ValueError("sphere_diameters_m must carry exactly 4 values (S1..S4)")
        if len(self.pairwise_distances_ext_m) != 6:
            raise ValueError("pairwise_distances_ext_m must carry exactly 6 values")
