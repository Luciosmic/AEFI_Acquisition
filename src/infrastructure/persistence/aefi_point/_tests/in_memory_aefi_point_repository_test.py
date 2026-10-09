from datetime import datetime, timezone
from uuid import uuid4

from domain.aefi_point.aefi_point import AefiPoint
from domain.aefi_point.events.aefi_point_acquired.aefi_point_acquired import AefiPointAcquired
from domain.aefi_point.value_objects.aefi_point_id.aefi_point_id import AefiPointId
from domain.aefi_point.value_objects.sample.sample import Sample
from domain.shared_kernel.value_objects.acquisition.aefi_voltage_measurement import AefiVoltageMeasurement
from domain.shared_kernel.value_objects.geometric.position_2d import Position2D
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.unit_of_work.in_memory_unit_of_work import InMemoryUnitOfWork


def _point(scan_id, n=2) -> AefiPoint:
    return AefiPoint(AefiPointId(uuid4()), scan_id, Position2D(0.0, 0.0), n)


def _samples(n):
    m = AefiVoltageMeasurement(1, 1, 1, 1, 1, 1, timestamp=datetime(2026, 10, 9, tzinfo=timezone.utc))
    return [Sample(m) for _ in range(n)]


def _setup():
    bus = InMemoryEventBus()
    received = []
    bus.subscribe("aefipointacquired", received.append)
    return InMemoryUnitOfWork(bus), received


def test_add_get_and_list_by_scan():
    uow, _ = _setup()
    scan_a, scan_b = uuid4(), uuid4()
    p1, p2, p3 = _point(scan_a), _point(scan_a), _point(scan_b)
    with uow:
        for p in (p1, p2, p3):
            uow.aefi_points.add(p)
        assert uow.aefi_points.get(p1.id) is p1
        assert uow.aefi_points.get(AefiPointId(uuid4())) is None
        assert uow.aefi_points.list_by_scan(scan_a) == [p1, p2]


def test_event_published_after_commit_only():
    uow, received = _setup()
    point = _point(uuid4())
    with uow:
        uow.aefi_points.add(point)
        point.record_samples(_samples(2))
        assert received == []
        uow.commit()
    assert len(received) == 1 and isinstance(received[0], AefiPointAcquired)
    assert received[0].aefi_point_id == point.id


def test_nothing_published_on_rollback():
    uow, received = _setup()
    point = _point(uuid4())
    with uow:
        uow.aefi_points.add(point)
        point.record_samples(_samples(2))
    assert received == []


def test_point_fetched_in_a_later_transaction_publishes_its_event():
    uow, received = _setup()
    point = _point(uuid4())
    with uow:
        uow.aefi_points.add(point)
        uow.commit()
    with uow:
        uow.aefi_points.get(point.id).record_samples(_samples(2))
        uow.commit()
    assert len(received) == 1
