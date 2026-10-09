from uuid import uuid4

from domain.aefi_point.value_objects.aefi_point_id.aefi_point_id import AefiPointId
from domain.scan.scan import Scan
from domain.scan.value_objects.scan_id.scan_id import ScanId
from domain.step_scan.events.scan_completed.scan_completed import ScanCompleted
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.unit_of_work.in_memory_unit_of_work import InMemoryUnitOfWork


def test_add_get_and_event_published_after_commit():
    bus = InMemoryEventBus()
    received = []
    bus.subscribe("scancompleted", received.append)
    uow = InMemoryUnitOfWork(bus)
    scan = Scan(ScanId(uuid4()), 1)
    with uow:
        uow.scans.add(scan)
        assert uow.scans.get(scan.id) is scan
        assert uow.scans.get(ScanId(uuid4())) is None
        uow.commit()
    with uow:
        s = uow.scans.get(scan.id)
        s.start()
        s.mark_point_acquired(AefiPointId(uuid4()))
        assert received == []
        uow.commit()
    assert len(received) == 1 and isinstance(received[0], ScanCompleted)
