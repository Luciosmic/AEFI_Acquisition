import json
import pytest
from pathlib import Path

from infrastructure.config.config_bootstrapper import ConfigBootstrapper


@pytest.fixture
def dirs(tmp_path):
    templates = tmp_path / "config_templates"
    templates.mkdir()
    runtime = tmp_path / "configs"
    return templates, runtime


def test_copies_missing_configs(dirs):
    templates, runtime = dirs
    (templates / "aefi_device_config.json").write_text('{"schema_version": "2.0"}')
    (templates / "acquisition_config.json").write_text('{"schema_version": "1.0"}')

    copied = ConfigBootstrapper(templates, runtime).ensure_configs_exist()

    assert set(copied) == {"aefi_device_config.json", "acquisition_config.json"}
    assert (runtime / "aefi_device_config.json").exists()
    assert (runtime / "acquisition_config.json").exists()


def test_does_not_overwrite_existing_file(dirs):
    templates, runtime = dirs
    runtime.mkdir()
    (templates / "aefi_device_config.json").write_text('{"schema_version": "2.0"}')
    (runtime / "aefi_device_config.json").write_text('{"user_value": 42}')

    copied = ConfigBootstrapper(templates, runtime).ensure_configs_exist()

    assert copied == []
    assert json.loads((runtime / "aefi_device_config.json").read_text()) == {"user_value": 42}


def test_creates_runtime_dir_when_absent(dirs):
    templates, _ = dirs
    (templates / "scan_config.json").write_text("{}")
    runtime = templates.parent / "nested" / "configs"

    ConfigBootstrapper(templates, runtime).ensure_configs_exist()

    assert runtime.is_dir()


def test_ignores_non_json_files(dirs):
    templates, runtime = dirs
    (templates / "aefi_device_config.json").write_text("{}")
    (templates / "NOTE.md").write_text("note")
    (templates / "scan_default.json.example").write_text("{}")

    copied = ConfigBootstrapper(templates, runtime).ensure_configs_exist()

    assert copied == ["aefi_device_config.json"]
    assert not (runtime / "NOTE.md").exists()
    assert not (runtime / "scan_default.json.example").exists()


def test_returns_empty_when_all_configs_present(dirs):
    templates, runtime = dirs
    runtime.mkdir()
    (templates / "aefi_device_config.json").write_text("{}")
    (runtime / "aefi_device_config.json").write_text("{}")

    copied = ConfigBootstrapper(templates, runtime).ensure_configs_exist()

    assert copied == []
