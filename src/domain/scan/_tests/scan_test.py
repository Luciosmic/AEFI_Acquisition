from uuid import uuid4

import pytest

from domain.scan.errors.scan_already_completed_error import ScanAlreadyCompletedError
from domain.scan.errors.scan_already_started_error import ScanAlreadyStartedError
from domain.scan.errors.scan_not_started_error import ScanNotStartedError
from domain.scan.errors.scan_source_not_declared_error import ScanSourceNotDeclaredError
from domain.scan.scan import Scan
from domain.scan.value_objects.expected_source.expected_source import ExpectedSource
from domain.scan.value_objects.scan_id.scan_id import ScanId
from domain.scan.value_objects.scan_state.scan_state import ScanState
from domain.step_scan.events.scan_completed.scan_completed import ScanCompleted

POINT = "aefi_point"


def make_scan(n=2, total_points=None) -> Scan:
    return Scan(ScanId(uuid4()), {POINT: ExpectedSource(n)}, total_points or n)


def test_new_scan_is_pending_and_observable():
    scan = make_scan()
    assert scan.state is ScanState.PENDING
    assert scan.received(POINT) == frozenset()


def test_start_moves_to_started_once():
    scan = make_scan()
    scan.start()
    assert scan.state is ScanState.STARTED
    with pytest.raises(ScanAlreadyStartedError):
        scan.start()


def test_acquisition_before_start_is_refused():
    scan = make_scan()
    with pytest.raises(ScanNotStartedError):
        scan.mark_acquired(POINT, uuid4())
    assert scan.received(POINT) == frozenset()


def test_completes_only_when_all_expected_acquisitions_present():
    scan = make_scan(2)
    scan.start()
    assert scan.mark_acquired(POINT, uuid4()) is True
    assert scan.state is ScanState.STARTED
    assert scan.domain_events == []
    assert scan.mark_acquired(POINT, uuid4()) is True
    assert scan.state is ScanState.COMPLETED
    (event,) = scan.domain_events
    assert isinstance(event, ScanCompleted) and event.scan_id == scan.id and event.total_points == 2
    assert scan.domain_events == []


def test_completed_event_reports_grid_points_not_acquisition_count():
    scan = Scan(ScanId(uuid4()), {"aefi_line": ExpectedSource(3)}, total_points=12)
    scan.start()
    for _ in range(3):
        scan.mark_acquired("aefi_line", uuid4())
    (event,) = scan.domain_events
    assert event.total_points == 12


def test_duplicate_acquisition_is_a_noop_not_counted():
    scan = make_scan(2)
    scan.start()
    a = uuid4()
    assert scan.mark_acquired(POINT, a) is True
    assert scan.mark_acquired(POINT, a) is False
    assert scan.state is ScanState.STARTED
    assert len(scan.received(POINT)) == 1


def test_completed_scan_refuses_new_acquisition_but_tolerates_duplicate():
    scan = make_scan(1)
    scan.start()
    a = uuid4()
    scan.mark_acquired(POINT, a)
    assert scan.mark_acquired(POINT, a) is False
    with pytest.raises(ScanAlreadyCompletedError):
        scan.mark_acquired(POINT, uuid4())


def test_undeclared_source_is_refused():
    scan = make_scan(1)
    scan.start()
    with pytest.raises(ScanSourceNotDeclaredError):
        scan.mark_acquired("narda_point", uuid4())
    assert scan.state is ScanState.STARTED


def test_needs_every_required_source_to_complete():
    scan = Scan(
        ScanId(uuid4()), {POINT: ExpectedSource(1), "narda_point": ExpectedSource(2)}, total_points=2
    )
    scan.start()
    scan.mark_acquired(POINT, uuid4())
    scan.mark_acquired("narda_point", uuid4())
    assert scan.state is ScanState.STARTED
    scan.mark_acquired("narda_point", uuid4())
    assert scan.state is ScanState.COMPLETED
    assert len(scan.domain_events) == 1


def test_optional_source_is_recorded_but_does_not_gate_completion():
    scan = Scan(
        ScanId(uuid4()), {POINT: ExpectedSource(1), "narda_point": ExpectedSource(5, required=False)}, total_points=1
    )
    scan.start()
    scan.mark_acquired("narda_point", uuid4())
    assert scan.state is ScanState.STARTED
    scan.mark_acquired(POINT, uuid4())
    assert scan.state is ScanState.COMPLETED
    assert len(scan.received("narda_point")) == 1


def test_total_points_must_be_positive():
    with pytest.raises(ValueError):
        Scan(ScanId(uuid4()), {POINT: ExpectedSource(1)}, 0)


def test_at_least_one_required_source_is_declared():
    with pytest.raises(ValueError):
        Scan(ScanId(uuid4()), {}, 1)
    with pytest.raises(ValueError):
        Scan(ScanId(uuid4()), {POINT: ExpectedSource(1, required=False)}, 1)
