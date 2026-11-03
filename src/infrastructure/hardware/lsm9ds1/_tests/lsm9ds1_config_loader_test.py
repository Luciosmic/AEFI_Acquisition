import json
from pathlib import Path

import pytest

from infrastructure.hardware.lsm9ds1.lsm9ds1_config_loader import (
    SUPPORTED_SCHEMA_VERSION,
    Lsm9ds1Config,
    load_lsm9ds1_config,
)

REPO_TEMPLATE = Path(__file__).resolve().parents[5] / "config_templates" / "lsm9ds1_config.json"


def _write(tmp_path, **overrides):
    data = {
        "schema_version": SUPPORTED_SCHEMA_VERSION,
        "com_port": "COM9",
        "baudrate": {"value": 115200, "unit": "Bd"},
        "sensors": [{"name": "accelerometer", "unit": "[g]"}, {"name": "lidar", "unit": "mm"}],
        "rate_hz": {"value": 50, "unit": "Hz"},
    }
    data.update(overrides)
    path = tmp_path / "lsm9ds1_config.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_reads_port_baudrate_channels_and_rate(tmp_path):
    cfg = load_lsm9ds1_config(_write(tmp_path))
    assert cfg == Lsm9ds1Config(
        com_port="COM9", baudrate=115200, channels=("accelerometer", "lidar"), rate_hz=50
    )


def test_null_rate_means_keep_board_rate(tmp_path):
    cfg = load_lsm9ds1_config(_write(tmp_path, rate_hz={"value": None, "unit": "Hz"}))
    assert cfg.rate_hz is None


def test_unknown_schema_version_is_refused(tmp_path):
    with pytest.raises(ValueError, match="schema_version"):
        load_lsm9ds1_config(_write(tmp_path, schema_version="9.9"))


def test_unknown_sensor_is_refused(tmp_path):
    with pytest.raises(ValueError, match="sensor"):
        load_lsm9ds1_config(_write(tmp_path, sensors=[{"name": "thermometer", "unit": "Cel"}]))


def test_rate_outside_documented_values_is_refused(tmp_path):
    with pytest.raises(ValueError, match="rate_hz"):
        load_lsm9ds1_config(_write(tmp_path, rate_hz={"value": 17, "unit": "Hz"}))


def test_missing_com_port_is_refused(tmp_path):
    path = _write(tmp_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    del data["com_port"]
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="com_port"):
        load_lsm9ds1_config(path)


def test_repository_template_is_loadable_and_matches_validated_board_settings():
    cfg = load_lsm9ds1_config(REPO_TEMPLATE)
    assert cfg.com_port == "COM5"
    assert cfg.baudrate == 256000
    assert set(cfg.channels) == {"accelerometer", "gyroscope", "magnetometer", "lidar"}
    assert cfg.rate_hz is None
