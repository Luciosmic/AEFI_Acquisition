from uuid import uuid4

import pytest

from domain.aefi_point.value_objects.aefi_point_id.aefi_point_id import AefiPointId
from domain.scan.errors.scan_already_completed_error import ScanAlreadyCompletedError
from domain.scan.errors.scan_already_started_error import ScanAlreadyStartedError
from domain.scan.errors.scan_not_started_error import ScanNotStartedError
from domain.scan.scan import Scan
from domain.scan.value_objects.scan_id.scan_id import ScanId
from domain.scan.value_objects.scan_state.scan_state import ScanState
from domain.step_scan.events.scan_completed.scan_completed import ScanCompleted


def make_scan(n=2) -> Scan:
    return Scan(ScanId(uuid4()), n)


def pid() -> AefiPointId:
    return AefiPointId(uuid4())


def test_new_scan_is_pending_and_observable():
    scan = make_scan()
    assert scan.state is ScanState.PENDING
    assert scan.received_point_ids == frozenset()


def test_start_moves_to_started_once():
    scan = make_scan()
    scan.start()
    assert scan.state is ScanState.STARTED
    with pytest.raises(ScanAlreadyStartedError):
        scan.start()


def test_point_before_start_is_refused():
    scan = make_scan()
    with pytest.raises(ScanNotStartedError):
        scan.mark_point_acquired(pid())
    assert scan.received_point_ids == frozenset()


def test_completes_only_when_all_expected_points_present():
    scan = make_scan(2)
    scan.start()
    assert scan.mark_point_acquired(pid()) is True
    assert scan.state is ScanState.STARTED
    assert scan.domain_events == []
    assert scan.mark_point_acquired(pid()) is True
    assert scan.state is ScanState.COMPLETED
    (event,) = scan.domain_events
    assert isinstance(event, ScanCompleted) and event.scan_id == scan.id and event.total_points == 2
    assert scan.domain_events == []


def test_duplicate_point_is_a_noop_not_counted():
    scan = make_scan(2)
    scan.start()
    p = pid()
    assert scan.mark_point_acquired(p) is True
    assert scan.mark_point_acquired(p) is False
    assert scan.state is ScanState.STARTED
    assert len(scan.received_point_ids) == 1


def test_completed_scan_refuses_new_point_but_tolerates_duplicate():
    scan = make_scan(1)
    scan.start()
    p = pid()
    scan.mark_point_acquired(p)
    assert scan.mark_point_acquired(p) is False
    with pytest.raises(ScanAlreadyCompletedError):
        scan.mark_point_acquired(pid())


def test_expected_points_must_be_positive():
    with pytest.raises(ValueError):
        make_scan(0)
