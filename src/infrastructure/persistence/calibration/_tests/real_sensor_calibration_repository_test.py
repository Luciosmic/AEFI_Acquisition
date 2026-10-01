import json
from uuid import uuid4

from domain.calibration.entities.sensor_calibration_entry.sensor_calibration_entry import (
    SensorCalibrationEntry,
)
from domain.calibration.value_objects.rotation_convention.rotation_convention import RotationConvention
from domain.calibration.value_objects.sensor_rotation_angles.sensor_rotation_angles import (
    SensorRotationAngles,
)
from infrastructure.persistence.calibration.real_sensor_calibration_repository import (
    RealSensorCalibrationRepository,
)

SENSOR_MOUNTING = uuid4()
SOURCE_GEOMETRY = uuid4()


def _make_entry(sensor_mounting=SENSOR_MOUNTING, geometry=SOURCE_GEOMETRY) -> SensorCalibrationEntry:
    return SensorCalibrationEntry.single(
        sensor_mounting_id=sensor_mounting,
        source_geometry_entry_id=geometry,
        angles=SensorRotationAngles(theta_x_degrees=35.3, theta_y_degrees=45.0, theta_z_degrees=0.9),
    )


def _make_repository(tmp_path) -> RealSensorCalibrationRepository:
    return RealSensorCalibrationRepository(storage_path=tmp_path / "sensor_calibration.json")


def test_find_all_returns_empty_list_when_none_recorded(tmp_path):
    assert _make_repository(tmp_path).find_all() == []


def test_add_then_find_all_round_trips_entries_in_order(tmp_path):
    repository = _make_repository(tmp_path)
    first = _make_entry()
    second = _make_entry(sensor_mounting=uuid4(), geometry=uuid4())  # remounted sensor, new geometry

    repository.add(first)
    repository.add(second)

    assert repository.find_all() == [first, second]


def test_storage_file_references_mounting_and_geometry_by_identity(tmp_path):
    repository = _make_repository(tmp_path)
    entry = _make_entry()

    repository.add(entry)

    stored = json.loads((tmp_path / "sensor_calibration.json").read_text(encoding="utf-8"))["entries"][0]
    assert stored == {
        "entry_id": str(entry.entry_id),
        "sensor_mounting_id": str(SENSOR_MOUNTING),
        "source_geometry_entry_id": str(SOURCE_GEOMETRY),
        "angles": {
            "theta_x_degrees": 35.3,
            "theta_y_degrees": 45.0,
            "theta_z_degrees": 0.9,
            "convention": {"type": "extrinsic", "order": "ZYX", "direction": "sources_to_sensor"},
        },
        "recorded_at": entry.recorded_at.isoformat(),
    }


def test_round_trip_preserves_convention(tmp_path):
    repository = _make_repository(tmp_path)
    repository.add(_make_entry())

    assert repository.find_all()[0].angles.convention == RotationConvention.standard()


def test_entry_without_convention_is_rejected(tmp_path, caplog):
    """No silent assumption about how angles without a convention must be read:
    the entry is rejected — skipped with an ERROR, not read with a guessed convention."""
    repository = _make_repository(tmp_path)
    repository.add(_make_entry())
    storage_path = tmp_path / "sensor_calibration.json"
    raw = json.loads(storage_path.read_text(encoding="utf-8"))
    del raw["entries"][0]["angles"]["convention"]
    storage_path.write_text(json.dumps(raw), encoding="utf-8")

    assert repository.find_all() == []
    assert "Skipping unreadable sensor calibration entry" in caplog.text


def test_unreadable_entry_is_skipped_not_fatal(tmp_path):
    """One entry under an unsupported rotation convention must not take the
    whole registry (and the application start) down."""
    repository = _make_repository(tmp_path)
    good = _make_entry()
    repository.add(_make_entry())
    repository.add(good)
    storage_path = tmp_path / "sensor_calibration.json"
    raw = json.loads(storage_path.read_text(encoding="utf-8"))
    raw["entries"][0]["angles"]["convention"]["order"] = "XYZ"
    storage_path.write_text(json.dumps(raw), encoding="utf-8")

    assert [e.entry_id for e in repository.find_all()] == [good.entry_id]


def test_add_handles_missing_parent_directory(tmp_path):
    storage_path = tmp_path / "nested" / "does" / "not" / "exist.json"
    repository = RealSensorCalibrationRepository(storage_path=storage_path)

    repository.add(_make_entry())

    assert storage_path.exists()
    assert len(repository.find_all()) == 1


def test_find_recovers_from_corrupt_file(tmp_path):
    storage_path = tmp_path / "sensor_calibration.json"
    storage_path.write_text("not valid json", encoding="utf-8")

    assert RealSensorCalibrationRepository(storage_path=storage_path).find_all() == []
