import json
from pathlib import Path

import pytest

from domain.calibration.value_objects.rotation_convention.rotation_convention import RotationConvention
from infrastructure.persistence.calibration.ideal_sensor_rotation_reader import IdealSensorRotationReader


def _rotation_block(**overrides) -> dict:
    block = {
        "theta_x": 35.3,
        "theta_y": 45,
        "theta_z": 0,
        "unit": "deg",
        "convention": {"type": "extrinsic", "order": "ZYX", "direction": "sources_to_sensor"},
    }
    block.update(overrides)
    return block


def _write_config(tmp_path: Path, rotation_block: dict) -> Path:
    path = tmp_path / "aefi_device_config.json"
    path.write_text(
        json.dumps({"sensor": {"calibration": {"sources_to_sensor_rotation": rotation_block}}}),
        encoding="utf-8",
    )
    return path


def test_reads_angles_and_convention(tmp_path):
    angles = IdealSensorRotationReader().read(_write_config(tmp_path, _rotation_block()))

    assert (angles.theta_x_degrees, angles.theta_y_degrees, angles.theta_z_degrees) == (35.3, 45.0, 0.0)
    assert angles.convention == RotationConvention.standard()


def test_reads_the_real_template():
    angles = IdealSensorRotationReader().read()

    assert angles.convention == RotationConvention.standard()


def test_rejects_missing_convention(tmp_path):
    block = _rotation_block()
    del block["convention"]

    with pytest.raises(ValueError, match="convention"):
        IdealSensorRotationReader().read(_write_config(tmp_path, block))


def test_rejects_missing_angle(tmp_path):
    block = _rotation_block()
    del block["theta_y"]

    with pytest.raises(ValueError, match="theta_y"):
        IdealSensorRotationReader().read(_write_config(tmp_path, block))


def test_rejects_unsupported_convention(tmp_path):
    block = _rotation_block(convention={"type": "extrinsic", "order": "XYZ", "direction": "sources_to_sensor"})

    with pytest.raises(ValueError, match="Unsupported rotation convention"):
        IdealSensorRotationReader().read(_write_config(tmp_path, block))
