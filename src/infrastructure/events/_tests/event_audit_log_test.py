import json
from dataclasses import dataclass
from uuid import UUID, uuid4

from domain.shared_kernel.events.domain_event import DomainEvent
from infrastructure.events.event_audit_log import EventAuditLog
from infrastructure.events.in_memory_event_bus import InMemoryEventBus


@dataclass(frozen=True)
class _SampleScanEvent(DomainEvent):
    scan_id: UUID = None


def test_record_appends_one_jsonl_line_per_event(tmp_path):
    audit_log = EventAuditLog(tmp_path)
    scan_id = uuid4()
    event = _SampleScanEvent(scan_id=scan_id)

    audit_log.record(event)

    lines = audit_log._path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    row = json.loads(lines[0])
    assert row["event_type"] == "_SampleScanEvent"
    assert row["scan_id"] == str(scan_id)
    assert "event_id" in row
    assert "occurred_on" in row


def test_wired_through_event_bus_wildcard_subscription(tmp_path):
    bus = InMemoryEventBus()
    audit_log = EventAuditLog(tmp_path)
    bus.subscribe("*", audit_log.record)

    bus.publish("scanstarted", _SampleScanEvent(scan_id=uuid4()))
    bus.publish("scancompleted", _SampleScanEvent(scan_id=uuid4()))

    lines = audit_log._path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
