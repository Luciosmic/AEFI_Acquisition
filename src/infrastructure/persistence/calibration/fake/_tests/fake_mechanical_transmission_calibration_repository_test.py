from uuid import uuid4

from domain.calibration.entities.mechanical_transmission_calibration_entry.mechanical_transmission_calibration_entry import (
    MechanicalTransmissionCalibrationEntry,
)
from infrastructure.persistence.calibration.fake.fake_mechanical_transmission_calibration_repository import (
    FakeMechanicalTransmissionCalibrationRepository,
)


def test_add_then_find_all_round_trips_entries_in_order():
    repository = FakeMechanicalTransmissionCalibrationRepository()
    first = MechanicalTransmissionCalibrationEntry.single(uuid4(), uuid4(), 8, 3.5, 4.0, 69.76)
    second = MechanicalTransmissionCalibrationEntry.single(uuid4(), uuid4(), 16, 3.5, 4.0, 69.76)

    repository.add(first)
    repository.add(second)

    assert repository.find_all() == [first, second]


def test_find_all_returns_a_copy():
    repository = FakeMechanicalTransmissionCalibrationRepository()
    repository.find_all().append("intruder")

    assert repository.find_all() == []
