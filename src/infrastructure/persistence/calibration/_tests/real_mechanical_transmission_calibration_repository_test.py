from uuid import uuid4

from domain.calibration.entities.mechanical_transmission_calibration_entry.mechanical_transmission_calibration_entry import (
    MechanicalTransmissionCalibrationEntry,
)
from infrastructure.persistence.calibration.real_mechanical_transmission_calibration_repository import (
    RealMechanicalTransmissionCalibrationRepository,
)


def _make_repository(tmp_path):
    return RealMechanicalTransmissionCalibrationRepository(storage_path=tmp_path / "transmission.json")


def test_find_all_is_empty_when_nothing_recorded(tmp_path):
    assert _make_repository(tmp_path).find_all() == []


def test_add_then_find_all_round_trips_entries_in_order(tmp_path):
    repository = _make_repository(tmp_path)
    first = MechanicalTransmissionCalibrationEntry.single(uuid4(), uuid4(), 8, 3.5, 4.0, 69.76)
    second = MechanicalTransmissionCalibrationEntry.single(uuid4(), uuid4(), 16, 3.5, 4.0, 69.76)

    repository.add(first)
    repository.add(second)

    assert repository.find_all() == [first, second]


def test_corrupt_file_reads_as_empty(tmp_path):
    (tmp_path / "transmission.json").write_text("{not json", encoding="utf-8")

    assert _make_repository(tmp_path).find_all() == []
