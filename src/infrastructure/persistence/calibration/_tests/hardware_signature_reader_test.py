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


TEMPLATE = {
    "excitation": {"electronic_board_version": "undeclared_excitation_electronic_board", "dds_chip": "AD9106"},
    "sensor": {"name": "undeclared_sensor", "conditioning_board_version": "undeclared_conditioning_electronics_board"},
}


def test_read_maps_template_placeholders(tmp_path):
    signature = HardwareSignatureReader().read(_write_device_config(tmp_path, TEMPLATE))

    assert signature == HardwareSignature(
        excitation_electronics_board_name="undeclared_excitation_electronic_board",
        conditioning_electronics_board_name="undeclared_conditioning_electronics_board",
        sensor_name="undeclared_sensor",
    )


def test_read_missing_file_does_not_raise_its_own_error(tmp_path):
    """
    The reader itself never raises on a missing file: it maps to empty
    required fields. `HardwareSignature.__post_init__` then rejects those
    empty fields with its own ValueError — the VO's own validation doing its
    job for a genuinely missing/malformed config, not an extra error added
    by the reader.
    """
    with pytest.raises(ValueError, match="excitation_electronics_board_name"):
        HardwareSignatureReader().read(tmp_path / "does_not_exist.json")


def test_read_missing_keys_fall_back_to_empty_strings_then_vo_rejects_them(tmp_path):
    with pytest.raises(ValueError, match="excitation_electronics_board_name"):
        HardwareSignatureReader().read(_write_device_config(tmp_path, {}))


def test_read_missing_sensor_name_is_rejected_by_the_vo(tmp_path):
    config = {"excitation": TEMPLATE["excitation"], "sensor": {"conditioning_board_version": "cond_v4"}}

    with pytest.raises(ValueError, match="sensor_name"):
        HardwareSignatureReader().read(_write_device_config(tmp_path, config))


def test_read_uses_default_path_when_none_given(monkeypatch, tmp_path):
    monkeypatch.setattr(HardwareSignatureReader, "DEFAULT_PATH", _write_device_config(tmp_path, TEMPLATE))

    assert HardwareSignatureReader().read().sensor_name == "undeclared_sensor"


def test_real_template_holds_only_generic_names():
    """The template is not a source of truth: no specific board or sensor name."""
    signature = HardwareSignatureReader().read(
        Path(__file__).resolve().parents[5] / "config_templates" / "aefi_device_config.json"
    )

    assert signature.sensor_name == "undeclared_sensor"
    assert signature.excitation_electronics_board_name.startswith("undeclared_")
    assert signature.conditioning_electronics_board_name.startswith("undeclared_")
