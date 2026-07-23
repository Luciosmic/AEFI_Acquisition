"""
UI configuration store.

Responsibility:
- Persist and load lightweight UI/view preferences (scan and export
  defaults) as flat JSON files under `.aefi_acquisition/configs/`.
- Bootstrap the runtime export config from the versioned template in
  `config_templates/` on first run.

Rationale:
- Keeps file I/O out of Qt widgets, consistent with how hardware configs
  are handled in `infrastructure/hardware/*_advanced_configurator.py`.
"""

from __future__ import annotations

import json
import os
import shutil
from typing import Any, Dict


class UIConfigStore:
    SCAN_CONFIG_PATH = os.path.join(".aefi_acquisition", "configs", "scan_default_config.json")
    EXPORT_CONFIG_PATH = os.path.join(".aefi_acquisition", "configs", "export_default_config.json")
    EXPORT_CONFIG_TEMPLATE_PATH = os.path.join("config_templates", "export_default_config.json")

    def load_scan_config(self) -> Dict[str, Any]:
        """Return the `scan_config` section, or {} if missing/invalid."""
        try:
            with open(self.SCAN_CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f).get("scan_config", {})
        except (OSError, json.JSONDecodeError):
            return {}

    def load_export_config(self) -> Dict[str, Any]:
        """Return export defaults, seeding the runtime file from the template on first run."""
        self._init_export_config_from_template()
        try:
            with open(self.EXPORT_CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return {}

    def save_export_config(self, export_config: Dict[str, Any]) -> None:
        os.makedirs(os.path.dirname(self.EXPORT_CONFIG_PATH), exist_ok=True)
        with open(self.EXPORT_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(export_config, f, indent=2, ensure_ascii=False)

    def _init_export_config_from_template(self) -> None:
        if os.path.exists(self.EXPORT_CONFIG_PATH) or not os.path.exists(self.EXPORT_CONFIG_TEMPLATE_PATH):
            return
        os.makedirs(os.path.dirname(self.EXPORT_CONFIG_PATH), exist_ok=True)
        shutil.copyfile(self.EXPORT_CONFIG_TEMPLATE_PATH, self.EXPORT_CONFIG_PATH)
