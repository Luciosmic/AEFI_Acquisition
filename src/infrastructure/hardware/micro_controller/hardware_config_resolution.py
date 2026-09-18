"""
Hardware Config Resolution - Infrastructure Layer

Responsibility:
- Merge a hardware's default_config.json with its last_config.json into a
  single resolved config, used identically by the boot sequence and by the
  Hardware Advanced Config panels.

Rationale:
- Extracted after a bug where the boot sequence and the config panel each
  read/merged these two files differently, letting them silently diverge
  (panel showed a value the real hardware was never actually given).
"""

import json
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


def load_json_if_exists(path: str) -> dict:
    """Load a JSON file into a dict, or return {} if it doesn't exist."""
    if not os.path.exists(path):
        logger.debug("Config file not found, using empty defaults: %s", path)
        return {}
    with open(path, "r") as f:
        return json.load(f)


def resolve_config(default: dict, override: Optional[dict]) -> dict:
    """Deep-merge override into a copy of default (override wins), recursing
    into nested dicts (e.g. per-channel gain/phase/offset) instead of
    replacing them wholesale. Does not mutate either argument."""
    resolved = dict(default)
    if not override:
        return resolved
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(resolved.get(key), dict):
            resolved[key] = resolve_config(resolved[key], value)
        else:
            resolved[key] = value
    return resolved
