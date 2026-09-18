import json
from pathlib import Path

import pytest

from domain.calibration.value_objects.hardware_signature.hardware_signature import HardwareSignature
from infrastructure.persistence.calibration.hardware_signature_reader import HardwareSignatureReader


def _write_device_config(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "aefi_device_config.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f)
    return path


def test_read_maps_fields_from_real_schema(tmp_path):
    path = _write_device_config(
        tmp_path,
        {
            "excitation": {
                "electronic_board_version": "AmpliHT_opa462_v2_ASSOCE",
                "dds_chip": "ADS131A04",
            },
            "sensor": {
                "version": "v2b",
                "serial_number": "SN-1234",
                "conditioning_board_version": "Final_v4_ASSOCE",
            },
        },
    )

    signature = HardwareSignatureReader().read(path)

    assert signature == HardwareSignature(
        excitation_board_version="AmpliHT_opa462_v2_ASSOCE",
        conditioning_board_version="Final_v4_ASSOCE",
        sensor_version="v2b",
        sensor_serial_number="SN-1234",
    )


def test_read_maps_null_serial_number_to_none(tmp_path):
    path = _write_device_config(
        tmp_path,
        {
            "excitation": {"electronic_board_version": "board_v2"},
            "sensor": {
                "version": "v2b",
                "serial_number": None,
                "conditioning_board_version": "cond_v4",
            },
        },
    )

    signature = HardwareSignatureReader().read(path)

    assert signature.sensor_serial_number is None


def test_read_missing_file_does_not_raise_its_own_error(tmp_path):
    """
    The reader itself never raises on a missing file: it maps to empty
    required fields. `HardwareSignature.__post_init__` then rejects those
    empty fields with its own ValueError — that's the VO's own validation
    doing its job for a genuinely missing/malformed config, not an extra
    error added by the reader.
    """
    missing_path = tmp_path / "does_not_exist.json"

    with pytest.raises(ValueError, match="excitation_board_version"):
        HardwareSignatureReader().read(missing_path)


def test_read_missing_keys_fall_back_to_empty_strings_then_vo_rejects_them(tmp_path):
    path = _write_device_config(tmp_path, {})

    with pytest.raises(ValueError, match="excitation_board_version"):
        HardwareSignatureReader().read(path)


def test_read_missing_keys_partially_present_yields_empty_string_for_missing_ones(tmp_path):
    """
    A partially-populated config (some required fields present) proves the
    reader maps a missing key to "" rather than raising itself — the VO's
    own validation is what surfaces the problem, exercised here on a field
    that IS present (sensor_version) while others are missing.
    """
    path = _write_device_config(
        tmp_path,
        {
            "excitation": {"electronic_board_version": "board_v2"},
            "sensor": {"version": "v2b"},
        },
    )

    with pytest.raises(ValueError, match="conditioning_board_version"):
        HardwareSignatureReader().read(path)


def test_read_uses_default_path_when_none_given(monkeypatch, tmp_path):
    path = _write_device_config(
        tmp_path,
        {
            "excitation": {"electronic_board_version": "board_v2"},
            "sensor": {
                "version": "v2b",
                "serial_number": None,
                "conditioning_board_version": "cond_v4",
            },
        },
    )
    monkeypatch.setattr(HardwareSignatureReader, "DEFAULT_PATH", path)

    signature = HardwareSignatureReader().read()

    assert signature.sensor_version == "v2b"
