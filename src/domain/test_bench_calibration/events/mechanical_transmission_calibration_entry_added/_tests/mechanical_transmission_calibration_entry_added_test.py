from uuid import uuid4

import pytest

from domain.test_bench_calibration.entities.mechanical_transmission_calibration_entry.mechanical_transmission_calibration_entry import (
    MechanicalTransmissionCalibrationEntry,
)
from domain.test_bench_calibration.events.mechanical_transmission_calibration_entry_added.mechanical_transmission_calibration_entry_added import (
    MechanicalTransmissionCalibrationEntryAdded,
)


def make_entry():
    return MechanicalTransmissionCalibrationEntry.single(uuid4(), uuid4(), 16, 3.5, 4.0, 21.11)


def test_carries_entry():
    entry = make_entry()
    assert MechanicalTransmissionCalibrationEntryAdded(entry=entry).entry == entry


def test_is_frozen():
    event = MechanicalTransmissionCalibrationEntryAdded(entry=make_entry())
    with pytest.raises(Exception):
        event.entry = make_entry()
