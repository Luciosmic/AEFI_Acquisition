from datetime import datetime, timezone
from uuid import uuid4

import pytest

from domain.aefi_point.aefi_point import AefiPoint
from domain.aefi_point.errors.aefi_point_already_acquired_error import AefiPointAlreadyAcquiredError
from domain.aefi_point.errors.aefi_point_incomplete_error import AefiPointIncompleteError
from domain.aefi_point.events.aefi_point_acquired.aefi_point_acquired import AefiPointAcquired
from domain.aefi_point.value_objects.aefi_point_id.aefi_point_id import AefiPointId
from domain.aefi_point.value_objects.sample.sample import Sample
from domain.shared_kernel.value_objects.acquisition.aefi_voltage_measurement import AefiVoltageMeasurement
from domain.shared_kernel.value_objects.geometric.position_2d import Position2D


def make_sample(v: float = 1.0) -> Sample:
    return Sample(AefiVoltageMeasurement(v, v, v, v, v, v, timestamp=datetime(2026, 10, 9, tzinfo=timezone.utc)))


def make_point(n: int = 3) -> AefiPoint:
    return AefiPoint(AefiPointId(uuid4()), uuid4(), Position2D(1.0, 2.0), n)


def test_exactly_n_valid_samples_acquires_point_and_emits_event():
    point = make_point(3)
    point.record_samples([make_sample(1.0), make_sample(2.0), make_sample(3.0)])

    assert point.is_acquired
    assert point.measurement.voltage_x_in_phase == pytest.approx(2.0)
    (event,) = point.domain_events
    assert isinstance(event, AefiPointAcquired)
    assert event.aefi_point_id == point.id
    assert event.scan_id == point.scan_id
    assert event.position == Position2D(1.0, 2.0)
    assert event.samples_count == 3
    assert event.measurement_unit.endswith("/V")


def test_domain_events_property_clears_the_list():
    point = make_point(1)
    point.record_samples([make_sample()])
    assert len(point.domain_events) == 1
    assert point.domain_events == []


@pytest.mark.parametrize("count", [0, 2, 4])
def test_wrong_sample_count_is_refused_and_leaves_no_trace(count):
    point = make_point(3)
    with pytest.raises(AefiPointIncompleteError):
        point.record_samples([make_sample() for _ in range(count)])
    assert not point.is_acquired
    assert point.domain_events == []


def test_acquired_point_refuses_a_second_recording():
    point = make_point(1)
    point.record_samples([make_sample()])
    point.domain_events
    with pytest.raises(AefiPointAlreadyAcquiredError):
        point.record_samples([make_sample()])
    assert point.domain_events == []


def test_expected_samples_must_be_positive():
    with pytest.raises(ValueError):
        make_point(0)
