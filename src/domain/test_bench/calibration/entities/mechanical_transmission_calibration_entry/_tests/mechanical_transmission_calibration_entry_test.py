"""Tests for MechanicalTransmissionCalibrationEntry."""
from uuid import uuid4

import pytest

from domain.test_bench.calibration.entities.mechanical_transmission_calibration_entry.mechanical_transmission_calibration_entry import (
    MechanicalTransmissionCalibrationEntry,
)


def make_entry(**overrides):
    params = dict(
        motor_mounting_id=uuid4(),
        stepper_driver_mounting_id=uuid4(),
        microsteps=16,
        driver_current_a=3.5,
        driver_peak_current_a=4.0,
        microns_per_pulse=21.11,
    )
    params.update(overrides)
    return MechanicalTransmissionCalibrationEntry.single(**params)


def test_the_distance_per_pulse_is_kept_as_characterized():
    # Lidar measurement on the bench, TB6600 at 1/16.
    entry = make_entry()

    assert entry.microns_per_pulse == pytest.approx(21.11)
    assert entry.microsteps == 16


def test_current_below_motor_rating_is_reported_with_both_driver_values():
    warning = make_entry().driver_current_shortfall(rated_current_a=4.2)

    assert warning is not None
    assert "3.5" in warning and "4.0" in warning and "4.2" in warning


def test_current_at_motor_rating_is_not_reported():
    assert make_entry(driver_current_a=4.2, driver_peak_current_a=4.5).driver_current_shortfall(4.2) is None


def test_single_gives_each_entry_its_own_identity():
    assert make_entry().entry_id != make_entry().entry_id


@pytest.mark.parametrize("overrides", [
    {"microsteps": 0},
    {"driver_current_a": 0.0},
    {"driver_peak_current_a": 3.0},  # peak below the set current
    {"microns_per_pulse": 0.0},
])
def test_rejects_non_physical_values(overrides):
    with pytest.raises(ValueError):
        make_entry(**overrides)

