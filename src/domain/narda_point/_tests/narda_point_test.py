from datetime import datetime, timezone
from uuid import uuid4

import pytest

from domain.electric_field_probe.value_objects.field_measurement.field_measurement import FieldMeasurement
from domain.narda_point.errors.narda_point_already_acquired_error import NardaPointAlreadyAcquiredError
from domain.narda_point.errors.narda_point_incomplete_error import NardaPointIncompleteError
from domain.narda_point.events.narda_point_acquired.narda_point_acquired import NardaPointAcquired
from domain.narda_point.narda_point import NardaPoint
from domain.narda_point.value_objects.narda_point_id.narda_point_id import NardaPointId
from domain.shared_kernel.value_objects.geometric.position_2d import Position2D


def fm(v: float = 1.0) -> FieldMeasurement:
    return FieldMeasurement((v, 2 * v), datetime(2026, 10, 9, tzinfo=timezone.utc))


def make_point(n: int = 3, baseline: bool = False) -> NardaPoint:
    return NardaPoint(NardaPointId(uuid4()), uuid4(), Position2D(1.0, 2.0), 7, n, baseline, ("X", "Y"))


def test_exactly_n_samples_acquires_point_and_emits_event():
    point = make_point(3)
    point.record_samples([fm(1.0), fm(2.0), fm(3.0)])

    assert point.is_acquired
    assert point.field_measurement.components == pytest.approx((2.0, 4.0))
    assert point.baseline_field_measurement is None
    (event,) = point.domain_events
    assert isinstance(event, NardaPointAcquired)
    assert event.narda_point_id == point.id and event.scan_id == point.scan_id
    assert event.point_index == 7 and event.position == Position2D(1.0, 2.0)
    assert event.axis_labels == ("X", "Y") and event.samples_count == 3
    assert event.baseline_field_measurement is None


def test_domain_events_property_clears_the_list():
    point = make_point(1)
    point.record_samples([fm()])
    assert len(point.domain_events) == 1
    assert point.domain_events == []


@pytest.mark.parametrize("count", [0, 2, 4])
def test_wrong_sample_count_is_refused_and_leaves_no_trace(count):
    point = make_point(3)
    with pytest.raises(NardaPointIncompleteError):
        point.record_samples([fm() for _ in range(count)])
    assert not point.is_acquired and point.domain_events == []


def test_differential_point_requires_exactly_n_baseline_samples():
    point = make_point(2, baseline=True)
    point.record_samples([fm(1.0), fm(3.0)], [fm(10.0), fm(20.0)])
    (event,) = point.domain_events
    assert event.baseline_field_measurement.components == pytest.approx((15.0, 30.0))


@pytest.mark.parametrize("baseline", [None, [], [fm()]])
def test_missing_or_short_baseline_is_refused_when_expected(baseline):
    point = make_point(2, baseline=True)
    with pytest.raises(NardaPointIncompleteError):
        point.record_samples([fm(), fm()], baseline)
    assert not point.is_acquired


def test_baseline_is_refused_when_not_expected():
    point = make_point(2, baseline=False)
    with pytest.raises(NardaPointIncompleteError):
        point.record_samples([fm(), fm()], [fm(), fm()])
    assert not point.is_acquired


def test_acquired_point_refuses_a_second_recording():
    point = make_point(1)
    point.record_samples([fm()])
    with pytest.raises(NardaPointAlreadyAcquiredError):
        point.record_samples([fm()])


def test_expected_samples_must_be_positive():
    with pytest.raises(ValueError):
        make_point(0)
