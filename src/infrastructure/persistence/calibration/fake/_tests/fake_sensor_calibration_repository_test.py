from uuid import uuid4

from domain.calibration.entities.sensor_calibration_entry.sensor_calibration_entry import (
    SensorCalibrationEntry,
)
from domain.calibration.value_objects.sensor_rotation_angles.sensor_rotation_angles import (
    SensorRotationAngles,
)
from infrastructure.persistence.calibration.fake.fake_sensor_calibration_repository import (
    FakeSensorCalibrationRepository,
)


def _make_entry() -> SensorCalibrationEntry:
    return SensorCalibrationEntry.single(uuid4(), uuid4(), SensorRotationAngles(35.3, 45.0, 0.0))


def test_find_all_returns_empty_list_when_none_recorded():
    assert FakeSensorCalibrationRepository().find_all() == []


def test_add_is_append_only_in_insertion_order():
    repository = FakeSensorCalibrationRepository()
    first, second = _make_entry(), _make_entry()

    repository.add(first)
    repository.add(second)

    assert repository.find_all() == [first, second]
