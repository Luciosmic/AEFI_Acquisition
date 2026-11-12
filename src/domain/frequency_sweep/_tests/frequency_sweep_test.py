from datetime import datetime, timezone
from uuid import uuid4

import pytest

from domain.frequency_sweep.errors.frequency_already_acquired_error import FrequencyAlreadyAcquiredError
from domain.frequency_sweep.errors.frequency_not_in_grid_error import FrequencyNotInGridError
from domain.frequency_sweep.errors.frequency_point_incomplete_error import FrequencyPointIncompleteError
from domain.frequency_sweep.events.frequency_point_acquired.frequency_point_acquired import FrequencyPointAcquired
from domain.frequency_sweep.events.frequency_sweep_completed.frequency_sweep_completed import FrequencySweepCompleted
from domain.frequency_sweep.frequency_sweep import FrequencySweep
from domain.frequency_sweep.value_objects.frequency_grid.frequency_grid import FrequencyGrid
from domain.frequency_sweep.value_objects.frequency_sweep_id.frequency_sweep_id import FrequencySweepId
from domain.frequency_sweep.value_objects.frequency_sweep_role.frequency_sweep_role import FrequencySweepRole
from domain.frequency_sweep.value_objects.table_height.table_height import TableHeight
from domain.shared_kernel.value_objects.acquisition.aefi_voltage_measurement import AefiVoltageMeasurement

GRID = FrequencyGrid((100.0, 1000.0, 10000.0))


def make_measurement(v: float) -> AefiVoltageMeasurement:
    return AefiVoltageMeasurement(v, v, v, v, v, v, timestamp=datetime(2026, 11, 12, tzinfo=timezone.utc))


def make_sweep(n: int = 2) -> FrequencySweep:
    return FrequencySweep(
        FrequencySweepId(uuid4()), FrequencySweepRole.BACKGROUND, GRID, TableHeight(42.0), samples_per_frequency=n
    )


def test_a_grid_frequency_with_exactly_n_samples_is_averaged_and_announced():
    sweep = make_sweep(2)
    measurement = sweep.record_frequency_point(1000.0, [make_measurement(1.0), make_measurement(3.0)])

    assert measurement.voltage_x_in_phase == pytest.approx(2.0)
    assert sweep.points == ((1000.0, measurement),)
    (event,) = sweep.domain_events
    assert isinstance(event, FrequencyPointAcquired)
    assert (event.frequency_sweep_id, event.role, event.frequency_index, event.frequency_hz) == (
        sweep.id, "background", 1, 1000.0,
    )
    assert (event.samples_count, event.table_height_mm) == (2, 42.0)
    assert event.frequency_unit == "http://qudt.org/vocab/unit/HZ"
    assert event.measurement_unit == "http://qudt.org/vocab/unit/V"


def test_the_last_grid_frequency_completes_the_sweep_once():
    sweep = make_sweep(1)
    for f in (10000.0, 100.0):
        sweep.record_frequency_point(f, [make_measurement(f)])
    assert not sweep.is_completed
    sweep.domain_events

    sweep.record_frequency_point(1000.0, [make_measurement(1.0)])

    assert sweep.is_completed
    assert [f for f, _ in sweep.points] == [100.0, 1000.0, 10000.0]
    events = sweep.domain_events
    assert isinstance(events[-1], FrequencySweepCompleted)
    assert events[-1].frequency_count == 3


@pytest.mark.parametrize(
    "frequency, samples, error",
    [
        (500.0, 2, FrequencyNotInGridError),
        (1000.0, 1, FrequencyPointIncompleteError),
        (1000.0, 3, FrequencyPointIncompleteError),
    ],
)
def test_refused_points_leave_the_sweep_unchanged(frequency, samples, error):
    sweep = make_sweep(2)
    with pytest.raises(error):
        sweep.record_frequency_point(frequency, [make_measurement(1.0)] * samples)
    assert sweep.points == ()
    assert sweep.domain_events == []


def test_a_frequency_is_acquired_once():
    sweep = make_sweep(1)
    sweep.record_frequency_point(100.0, [make_measurement(1.0)])
    with pytest.raises(FrequencyAlreadyAcquiredError):
        sweep.record_frequency_point(100.0, [make_measurement(2.0)])
    assert sweep.points[0][1].voltage_x_in_phase == 1.0


def test_needs_at_least_one_sample_per_frequency():
    with pytest.raises(ValueError):
        make_sweep(0)
