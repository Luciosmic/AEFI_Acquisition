"""
LSM9DS1 board configuration loader

Responsibility:
- Read `lsm9ds1_config.json` (com port, baudrate, channels, optional stream
  rate) into a frozen Lsm9ds1Config; refuse an unknown schema_version.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from infrastructure.hardware.lsm9ds1.lsm9ds1_stream_protocol import (
    FIELD_COUNT,
    VALID_RATES_HZ,
)

logger = logging.getLogger(__name__)

SUPPORTED_SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class Lsm9ds1Config:
    com_port: str
    baudrate: int
    channels: Tuple[str, ...]
    rate_hz: Optional[int] = None


def _require(data: dict, key: str, path: Path):
    if key not in data:
        raise ValueError(f"{path}: missing required key '{key}'")
    return data[key]


def load_lsm9ds1_config(path: Path) -> Lsm9ds1Config:
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    version = data.get("schema_version")
    if version != SUPPORTED_SCHEMA_VERSION:
        raise ValueError(
            f"{path}: unsupported schema_version {version!r} "
            f"(supported: {SUPPORTED_SCHEMA_VERSION!r})"
        )

    com_port = str(_require(data, "com_port", path))
    baudrate = int(_require(data, "baudrate", path)["value"])

    channels = []
    for entry in _require(data, "sensors", path):
        name = entry["name"]
        if name not in FIELD_COUNT:
            raise ValueError(f"{path}: unknown sensor {name!r} (known: {sorted(FIELD_COUNT)})")
        channels.append(name)
    if not channels:
        raise ValueError(f"{path}: at least one sensor is required")

    rate_hz = _require(data, "rate_hz", path)["value"]
    if rate_hz is not None and rate_hz not in VALID_RATES_HZ:
        raise ValueError(f"{path}: rate_hz must be null or one of {VALID_RATES_HZ}, got {rate_hz!r}")

    config = Lsm9ds1Config(
        com_port=com_port, baudrate=baudrate, channels=tuple(channels), rate_hz=rate_hz
    )
    logger.info("LSM9DS1 config read from %s: %s", path, config)
    return config
