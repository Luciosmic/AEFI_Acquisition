"""
Acquisition Snapshot Reader

Responsibility:
- Implement `IAcquisitionSnapshotPort` by reading the known on-disk JSON
  config files that aren't otherwise exposed via an in-memory getter
  (AD9106 last-applied config, motion last-applied config) plus the static
  hardware identity/connection-defaults templates.

Rationale:
- Quick, dependency-free way to bundle "whatever is currently accessible"
  into the acquisition metadata JSON without new in-memory config services.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional


def _load_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


class AcquisitionSnapshotReader:
    """Reads the on-disk config sections available at acquisition time."""

    SOURCES = {
        "ad9106_last_config": Path(".aefi_acquisition/configs/ad9106_last_config.json"),
        "motion_last_config": Path(".aefi_acquisition/configs/motion_last_config.json"),
        "aefi_device_hardware_identity": Path("config_templates/aefi_device_config.json"),
        "electric_field_probe_connection_defaults": Path("config_templates/electric_field_probe_config.json"),
    }

    def read(self) -> Dict[str, Any]:
        snapshot: Dict[str, Any] = {}
        for key, path in self.SOURCES.items():
            content = _load_json(path)
            if content is not None:
                snapshot[key] = content
        return snapshot
