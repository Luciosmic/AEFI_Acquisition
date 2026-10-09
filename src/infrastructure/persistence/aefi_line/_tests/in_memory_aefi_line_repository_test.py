from datetime import datetime, timezone
from uuid import uuid4

from domain.aefi_line.aefi_line import AefiLine
from domain.aefi_line.events.aefi_line_acquired.aefi_line_acquired import AefiLineAcquired
from domain.aefi_line.value_objects.aefi_line_id.aefi_line_id import AefiLineId
from domain.aefi_line.value_objects.line_grid_point.line_grid_point import LineGridPoint
from domain.shared_kernel.value_objects.acquisition.aefi_voltage_measurement import AefiVoltageMeasurement
from domain.shared_kernel.value_objects.geometric.position_2d import Position2D
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.unit_of_work.in_memory_unit_of_work import InMemoryUnitOfWork

M = AefiVoltageMeasurement(1, 1, 1, 1, 1, 1, timestamp=datetime(2026, 10, 9, tzinfo=timezone.utc))


def _line(scan_id, index=0, n=2) -> AefiLine:
    return AefiLine(AefiLineId(uuid4()), scan_id, index, n)


def _points(n):
    return [LineGridPoint(k, Position2D(float(k), 0.0), M) for k in range(n)]


def _setup():
    bus = InMemoryEventBus()
    received = []
    bus.subscribe("aefilineacquired", received.append)
    return InMemoryUnitOfWork(bus), received


def test_add_get_and_list_by_scan_sorted_by_line_index():
    uow, _ = _setup()
    scan_a, scan_b = uuid4(), uuid4()
    l2, l0, other = _line(scan_a, 2), _line(scan_a, 0), _line(scan_b, 1)
    with uow:
        for line in (l2, l0, other):
            uow.aefi_lines.add(line)
        assert uow.aefi_lines.get(l2.id) is l2
        assert uow.aefi_lines.get(AefiLineId(uuid4())) is None
        assert uow.aefi_lines.list_by_scan(scan_a) == [l0, l2]


def test_event_published_after_commit_only():
    uow, received = _setup()
    line = _line(uuid4())
    with uow:
        uow.aefi_lines.add(line)
        line.record_points(_points(2))
        assert received == []
        uow.commit()
    assert len(received) == 1 and isinstance(received[0], AefiLineAcquired)
    assert received[0].aefi_line_id == line.id


def test_nothing_published_on_rollback():
    uow, received = _setup()
    line = _line(uuid4())
    with uow:
        uow.aefi_lines.add(line)
        line.record_points(_points(2))
    assert received == []
