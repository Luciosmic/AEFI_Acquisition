"""
Geometric Configuration Reader

Responsibility:
- Read `config_templates/aefi_device_config.json` (same file
  `HardwareSignatureReader` reads) and map its
  `excitation.sources_geometry` section onto the domain
  `GeometricConfigurationSignature` VO.

Rationale:
- No new config surface is introduced: the caliper-measured geometry used to
  seed the source geometry calibration registry reuses the existing device
  config template as-is.
- One-time seed only: since SourceGeometryCalibrationService became the live
  source of geometric configuration (its calibration registry is the source
  of truth), this reader is used ONCE by the composition root — only when
  ISourceGeometryCalibrationRepository.find_all() is empty on first boot — to
  seed the registry's first entry. It is never called for a live per-boot
  lookup anymore. See geometric_configuration_reader_intention.md.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from domain.calibration.value_objects.geometric_configuration_signature.geometric_configuration_signature import (
    GeometricConfigurationSignature,
)

logger = logging.getLogger(__name__)

_SPHERE_LABELS = ("S1", "S2", "S3", "S4")
_DISTANCE_LABELS = ("D_S1_S2", "D_S3_S4", "D_S1_S3", "D_S1_S4", "D_S2_S3", "D_S2_S4")


class GeometricConfigurationReader:
    """Maps `config_templates/aefi_device_config.json` to a `GeometricConfigurationSignature`."""

    DEFAULT_PATH = Path("config_templates/aefi_device_config.json")

    def read(self, path: Optional[Path] = None) -> GeometricConfigurationSignature:
        resolved_path = path or self.DEFAULT_PATH
        data = self._load_json(resolved_path)
        if not data:
            logger.warning("Geometric configuration source not found or empty: %s", resolved_path)

        sources_geometry = ((data.get("excitation") or {}).get("sources_geometry")) or {}
        sphere_diameters = sources_geometry.get("sphere_diameters") or {}
        pairwise_distances = sources_geometry.get("pairwise_distances_ext") or {}

        signature = GeometricConfigurationSignature(
            sphere_diameters_m=tuple(
                float((sphere_diameters.get(label) or {}).get("value", 0.0)) for label in _SPHERE_LABELS
            ),
            pairwise_distances_ext_m=tuple(
                float((pairwise_distances.get(label) or {}).get("value", 0.0)) for label in _DISTANCE_LABELS
            ),
        )
        logger.info("Geometric configuration read from %s: %s", resolved_path, signature)
        return signature

    @staticmethod
    def _load_json(path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
