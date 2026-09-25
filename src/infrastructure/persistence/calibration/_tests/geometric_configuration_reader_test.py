import json
from pathlib import Path

from domain.calibration.value_objects.geometric_configuration_signature.geometric_configuration_signature import (
    GeometricConfigurationSignature,
)
from infrastructure.persistence.calibration.geometric_configuration_reader import (
    GeometricConfigurationReader,
)


def _write_device_config(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "aefi_device_config.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f)
    return path


def _sources_geometry_block() -> dict:
    return {
        "sphere_diameters": {
            "S1": {"value": 0.0196, "unit": "m"},
            "S2": {"value": 0.0196, "unit": "m"},
            "S3": {"value": 0.0195, "unit": "m"},
            "S4": {"value": 0.0195, "unit": "m"},
        },
        "pairwise_distances_ext": {
            "D_S1_S2": {"value": 0.11142, "unit": "m"},
            "D_S3_S4": {"value": 0.10908, "unit": "m"},
            "D_S1_S3": {"value": 0.08436, "unit": "m"},
            "D_S1_S4": {"value": 0.08352, "unit": "m"},
            "D_S2_S3": {"value": 0.08230, "unit": "m"},
            "D_S2_S4": {"value": 0.08450, "unit": "m"},
        },
    }


def test_read_maps_fields_from_real_schema(tmp_path):
    path = _write_device_config(
        tmp_path, {"excitation": {"sources_geometry": _sources_geometry_block()}}
    )

    signature = GeometricConfigurationReader().read(path)

    assert signature == GeometricConfigurationSignature(
        sphere_diameters_m=(0.0196, 0.0196, 0.0195, 0.0195),
        pairwise_distances_ext_m=(0.11142, 0.10908, 0.08436, 0.08352, 0.08230, 0.08450),
    )


def test_read_missing_file_falls_back_to_zeros(tmp_path):
    missing_path = tmp_path / "does_not_exist.json"

    signature = GeometricConfigurationReader().read(missing_path)

    assert signature == GeometricConfigurationSignature(
        sphere_diameters_m=(0.0, 0.0, 0.0, 0.0),
        pairwise_distances_ext_m=(0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    )


def test_read_missing_section_falls_back_to_zeros(tmp_path):
    path = _write_device_config(tmp_path, {})

    signature = GeometricConfigurationReader().read(path)

    assert signature.sphere_diameters_m == (0.0, 0.0, 0.0, 0.0)


def test_read_partially_present_geometry_defaults_missing_values(tmp_path):
    block = _sources_geometry_block()
    del block["sphere_diameters"]["S4"]
    path = _write_device_config(tmp_path, {"excitation": {"sources_geometry": block}})

    signature = GeometricConfigurationReader().read(path)

    assert signature.sphere_diameters_m == (0.0196, 0.0196, 0.0195, 0.0)


def test_read_uses_default_path_when_none_given(monkeypatch, tmp_path):
    path = _write_device_config(
        tmp_path, {"excitation": {"sources_geometry": _sources_geometry_block()}}
    )
    monkeypatch.setattr(GeometricConfigurationReader, "DEFAULT_PATH", path)

    signature = GeometricConfigurationReader().read()

    assert signature.sphere_diameters_m == (0.0196, 0.0196, 0.0195, 0.0195)
