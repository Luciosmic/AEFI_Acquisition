import json
from uuid import uuid4

from domain.test_bench_calibration.entities.mechanical_transmission_calibration_entry.mechanical_transmission_calibration_entry import (
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
    first = MechanicalTransmissionCalibrationEntry.single(uuid4(), uuid4(), 8, 3.5, 4.0, 21.11)
    second = MechanicalTransmissionCalibrationEntry.single(uuid4(), uuid4(), 16, 3.5, 4.0, 21.11)

    repository.add(first)
    repository.add(second)

    assert repository.find_all() == [first, second]


def test_corrupt_file_reads_as_empty(tmp_path):
    (tmp_path / "transmission.json").write_text("{not json", encoding="utf-8")

    assert _make_repository(tmp_path).find_all() == []


def test_legacy_entry_with_a_travel_per_revolution_is_ignored_but_kept_in_the_file(tmp_path):
    """Before 2026-11-10 an entry held a travel per motor revolution: never a measured µm/pulse."""
    legacy = {
        "entry_id": "8f45b39d-9e2e-4959-be22-f2a1bb08f737",
        "motor_mounting_id": str(uuid4()),
        "stepper_driver_mounting_id": str(uuid4()),
        "microsteps": 16,
        "driver_current_a": 3.5,
        "driver_peak_current_a": 4.0,
        "travel_per_motor_revolution_mm": 69.76,
        "recorded_at": "2026-10-06T15:58:02.715317+00:00",
    }
    (tmp_path / "transmission.json").write_text(json.dumps({"entries": [legacy]}), encoding="utf-8")
    repository = _make_repository(tmp_path)

    assert repository.find_all() == []

    current = MechanicalTransmissionCalibrationEntry.single(uuid4(), uuid4(), 16, 3.5, 4.0, 21.11)
    repository.add(current)

    assert repository.find_all() == [current]
    assert json.loads((tmp_path / "transmission.json").read_text(encoding="utf-8"))["entries"][0] == legacy
