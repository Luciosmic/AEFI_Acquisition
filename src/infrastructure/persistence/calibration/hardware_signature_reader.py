"""
Hardware Signature Reader

Responsibility:
- Read `config_templates/aefi_device_config.json` (the same file
  `AcquisitionSnapshotReader` bundles into export metadata) and map its
  `excitation`/`sensor` sections onto the domain `HardwareSignature` VO.

Rationale:
- No new config surface is introduced: the hardware identity used to tag
  calibration entries reuses the existing device config template as-is.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from domain.calibration.value_objects.hardware_signature.hardware_signature import HardwareSignature

logger = logging.getLogger(__name__)


class HardwareSignatureReader:
    """Maps `config_templates/aefi_device_config.json` to a `HardwareSignature`."""

    DEFAULT_PATH = Path("config_templates/aefi_device_config.json")

    def read(self, path: Optional[Path] = None) -> HardwareSignature:
        resolved_path = path or self.DEFAULT_PATH
        data = self._load_json(resolved_path)
        if not data:
            logger.warning("Hardware signature source not found or empty: %s", resolved_path)

        excitation = data.get("excitation") or {}
        sensor = data.get("sensor") or {}

        signature = HardwareSignature(
            excitation_electronics_board_name=excitation.get("electronic_board_version") or "",
            conditioning_electronics_board_name=sensor.get("conditioning_board_version") or "",
            sensor_name=sensor.get("name") or "",
        )
        logger.info("Hardware signature read from %s: %s", resolved_path, signature)
        return signature

    @staticmethod
    def _load_json(path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
