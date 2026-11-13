import dataclasses
import math

import pytest

from domain.scan.value_objects.column_rest_criterion.column_rest_criterion import ColumnRestCriterion


def test_defaults_are_the_banc_test_ii_settings_and_frozen() -> None:
    criterion = ColumnRestCriterion()
    assert (criterion.rest_measurement_s, criterion.window_s, criterion.factor, criterion.timeout_s) == (
        10.0, 1.0, 1.5, 30.0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        criterion.factor = 2.0


@pytest.mark.parametrize("field", ["rest_measurement_s", "window_s", "timeout_s"])
def test_durations_must_be_positive(field):
    with pytest.raises(ValueError):
        ColumnRestCriterion(**{field: 0.0})


def test_factor_below_one_would_never_be_reached_at_rest() -> None:
    with pytest.raises(ValueError):
        ColumnRestCriterion(factor=0.9)


def test_at_rest_up_to_factor_times_the_rest_level() -> None:
    criterion = ColumnRestCriterion(factor=1.5)
    assert criterion.threshold_g(0.004) == pytest.approx(0.006)
    assert criterion.is_at_rest(0.006, 0.004)
    assert not criterion.is_at_rest(0.0061, 0.004)


def test_vibration_ignores_gravity_and_static_offset() -> None:
    still_tilted = [(0.1, 0.2, 1.03)] * 5
    assert ColumnRestCriterion.vibration_g(still_tilted) == pytest.approx(0.0)


def test_vibration_is_rms_of_deviation_from_mean_vector() -> None:
    # x alternates ±0.01 g around 0, y and z constant: population σx = 0.01.
    samples = [(0.01, 0.0, 1.0), (-0.01, 0.0, 1.0)] * 4
    assert ColumnRestCriterion.vibration_g(samples) == pytest.approx(0.01)
    # Same deviation on the three axes: sqrt(3) × σ.
    samples = [(0.01, 0.01, 1.01), (-0.01, -0.01, 0.99)]
    assert ColumnRestCriterion.vibration_g(samples) == pytest.approx(0.01 * math.sqrt(3))


def test_no_vibration_under_two_samples() -> None:
    assert ColumnRestCriterion.vibration_g([]) is None
    assert ColumnRestCriterion.vibration_g([(0.0, 0.0, 1.0)]) is None
