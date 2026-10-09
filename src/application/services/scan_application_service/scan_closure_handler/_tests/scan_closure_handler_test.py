import logging
from datetime import datetime, timezone
from uuid import uuid4

from application.services.scan_application_service.scan_closure_handler.scan_closure_handler import ScanClosureHandler
from domain.aefi_point.aefi_point import AefiPoint
from domain.aefi_point.value_objects.aefi_point_id.aefi_point_id import AefiPointId
from domain.aefi_point.value_objects.sample.sample import Sample
from domain.scan.events.scan_closure_failed.scan_closure_failed import ScanClosureFailed
from domain.scan.scan import Scan
from domain.scan.value_objects.scan_id.scan_id import ScanId
from domain.scan.value_objects.scan_state.scan_state import ScanState
from domain.shared_kernel.value_objects.acquisition.aefi_voltage_measurement import AefiVoltageMeasurement
from domain.shared_kernel.value_objects.geometric.position_2d import Position2D
from domain.step_scan.events.scan_completed.scan_completed import ScanCompleted
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.unit_of_work.in_memory_unit_of_work import InMemoryUnitOfWork


def _samples(n=2):
    m = AefiVoltageMeasurement(1, 1, 1, 1, 1, 1, timestamp=datetime(2026, 10, 9, tzinfo=timezone.utc))
    return [Sample(m) for _ in range(n)]


def _setup():
    bus = InMemoryEventBus()
    uow = InMemoryUnitOfWork(bus)
    ScanClosureHandler(bus, uow)
    completed, failed = [], []
    bus.subscribe("scancompleted", completed.append)
    bus.subscribe("scanclosurefailed", failed.append)
    return uow, completed, failed


def _acquire(uow, scan_id, point=None):
    point = point or AefiPoint(AefiPointId(uuid4()), scan_id, Position2D(0.0, 0.0), 2)
    with uow:
        uow.aefi_points.add(point)
        point.record_samples(_samples(2))
        uow.commit()
    return point


def test_three_points_complete_the_scan_through_separate_transactions():
    uow, completed, failed = _setup()
    scan = Scan(ScanId(uuid4()), 3)
    with uow:
        uow.scans.add(scan)
        scan.start()
        uow.commit()

    for _ in range(3):
        assert completed == []
        _acquire(uow, scan.id)

    assert scan.state is ScanState.COMPLETED
    assert len(scan.received_point_ids) == 3
    assert len(completed) == 1 and isinstance(completed[0], ScanCompleted) and completed[0].scan_id == scan.id
    assert failed == []


def test_unknown_scan_publishes_closure_failed_without_propagating():
    uow, completed, failed = _setup()
    scan_id = uuid4()
    point = _acquire(uow, scan_id)

    assert completed == []
    (event,) = failed
    assert isinstance(event, ScanClosureFailed)
    assert event.scan_id == scan_id and event.aefi_point_id == point.id and "introuvable" in event.reason


def test_point_received_before_scan_start_publishes_closure_failed():
    uow, completed, failed = _setup()
    scan = Scan(ScanId(uuid4()), 1)
    with uow:
        uow.scans.add(scan)
        uow.commit()
    _acquire(uow, scan.id)

    assert scan.state is ScanState.PENDING
    assert len(failed) == 1 and "ScanNotStartedError" in failed[0].reason


def test_duplicate_event_is_a_logged_noop(caplog):
    uow, completed, failed = _setup()
    scan = Scan(ScanId(uuid4()), 2)
    with uow:
        uow.scans.add(scan)
        scan.start()
        uow.commit()
    point = _acquire(uow, scan.id)

    handler_event = _first_event(point)
    with caplog.at_level(logging.INFO):
        uow._event_bus.publish("aefipointacquired", handler_event)

    assert len(scan.received_point_ids) == 1
    assert failed == [] and completed == []
    assert "rien a faire" in caplog.text


def _first_event(point):
    from domain.aefi_point.events.aefi_point_acquired.aefi_point_acquired import AefiPointAcquired

    return AefiPointAcquired(
        aefi_point_id=point.id, scan_id=point.scan_id, position=point.position,
        measurement=point.measurement, samples_count=point.expected_samples,
    )
