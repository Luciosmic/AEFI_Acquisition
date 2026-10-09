from datetime import datetime, timezone
from uuid import uuid4

import pytest

from domain.aefi_line.aefi_line import AefiLine
from domain.aefi_line.errors.aefi_line_already_acquired_error import AefiLineAlreadyAcquiredError
from domain.aefi_line.errors.aefi_line_incomplete_error import AefiLineIncompleteError
from domain.aefi_line.events.aefi_line_acquired.aefi_line_acquired import AefiLineAcquired
from domain.aefi_line.value_objects.aefi_line_id.aefi_line_id import AefiLineId
from domain.aefi_line.value_objects.line_grid_point.line_grid_point import LineGridPoint
from domain.shared_kernel.value_objects.acquisition.aefi_voltage_measurement import AefiVoltageMeasurement
from domain.shared_kernel.value_objects.geometric.position_2d import Position2D

M = AefiVoltageMeasurement(1, 1, 1, 1, 1, 1, timestamp=datetime(2026, 10, 9, tzinfo=timezone.utc))


def gp(k: int) -> LineGridPoint:
    return LineGridPoint(k, Position2D(float(k), 0.0), M)


def make_line(n=3) -> AefiLine:
    return AefiLine(AefiLineId(uuid4()), uuid4(), 1, n)


def test_all_grid_points_acquire_the_line_and_emit_the_event():
    line = make_line(3)
    line.record_points([gp(2), gp(0), gp(1)])

    assert line.is_acquired and [p.index_in_line for p in line.points] == [0, 1, 2]
    (event,) = line.domain_events
    assert isinstance(event, AefiLineAcquired)
    assert event.aefi_line_id == line.id and event.scan_id == line.scan_id
    assert event.line_index == 1 and event.points_count == 3 and event.points == line.points
    assert line.domain_events == []


def test_missing_point_is_refused_and_leaves_no_state():
    line = make_line(3)
    with pytest.raises(AefiLineIncompleteError) as e:
        line.record_points([gp(0), gp(2)])
    assert e.value.missing_indices == (1,) and e.value.expected == 3
    assert not line.is_acquired and line.domain_events == []


def test_duplicate_or_out_of_range_index_is_refused():
    with pytest.raises(AefiLineIncompleteError):
        make_line(3).record_points([gp(0), gp(1), gp(1)])
    with pytest.raises(AefiLineIncompleteError):
        make_line(2).record_points([gp(0), gp(1), gp(2)])


def test_second_attempt_is_refused():
    line = make_line(1)
    line.record_points([gp(0)])
    with pytest.raises(AefiLineAlreadyAcquiredError):
        line.record_points([gp(0)])


def test_expected_points_must_be_positive():
    with pytest.raises(ValueError):
        make_line(0)
