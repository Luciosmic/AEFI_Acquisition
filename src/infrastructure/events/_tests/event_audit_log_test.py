import json
import threading
import time
from dataclasses import dataclass
from uuid import UUID, uuid4

from domain.shared_kernel.events.domain_event.domain_event import DomainEvent
from infrastructure.events.event_audit_log import EventAuditLog
from infrastructure.in_memory_event_bus.in_memory_event_bus import InMemoryEventBus


@dataclass(frozen=True)
class _SampleScanEvent(DomainEvent):
    scan_id: UUID = None


def test_record_appends_one_jsonl_line_per_event(tmp_path):
    audit_log = EventAuditLog(tmp_path)
    scan_id = uuid4()
    event = _SampleScanEvent(scan_id=scan_id)

    audit_log.record(event)
    audit_log.flush()

    lines = audit_log._path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    row = json.loads(lines[0])
    assert row["event_type"] == "_SampleScanEvent"
    assert row["scan_id"] == str(scan_id)
    assert "event_id" in row
    assert "occurred_on" in row
    audit_log.close()


def test_wired_through_event_bus_wildcard_subscription(tmp_path):
    bus = InMemoryEventBus()
    audit_log = EventAuditLog(tmp_path)
    bus.subscribe("*", audit_log.record)

    bus.publish("scanstarted", _SampleScanEvent(scan_id=uuid4()))
    bus.publish("scancompleted", _SampleScanEvent(scan_id=uuid4()))
    audit_log.flush()

    lines = audit_log._path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    audit_log.close()


@dataclass(frozen=True)
class _BulkySampleEvent(DomainEvent):
    thread_index: int = 0
    sample_index: int = 0
    padding: str = ""


def test_concurrent_publishers_never_corrupt_a_line(tmp_path):
    """The bus publishes from the scan loop and the hardware threads at once
    (bench 2026-10-30: one line overwritten mid-fly-scan)."""
    n_threads, n_events = 8, 500
    audit_log = EventAuditLog(tmp_path)
    start = threading.Barrier(n_threads)

    def publish(thread_index):
        start.wait()
        for sample_index in range(n_events):
            audit_log.record(_BulkySampleEvent(
                thread_index=thread_index, sample_index=sample_index, padding="x" * 400,
            ))

    threads = [threading.Thread(target=publish, args=(i,)) for i in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    audit_log.flush()

    lines = audit_log.path.read_text(encoding="utf-8").splitlines()
    invalid = []
    for number, line in enumerate(lines, 1):
        try:
            json.loads(line)
        except json.JSONDecodeError:
            invalid.append(number)
    assert invalid == []
    assert len(lines) == n_threads * n_events
    audit_log.close()


def test_record_does_not_wait_on_the_disk(tmp_path):
    """The acquisition thread publishes ~3 events per point: recording must
    cost microseconds, not one file open each (~0.55 ms measured 2026-11-27)."""
    audit_log = EventAuditLog(tmp_path)
    n_events = 2000

    t0 = time.perf_counter()
    for index in range(n_events):
        audit_log.record(_BulkySampleEvent(sample_index=index))
    per_event_ms = (time.perf_counter() - t0) / n_events * 1e3

    assert per_event_ms < 0.05
    audit_log.flush()
    assert len(audit_log.path.read_text(encoding="utf-8").splitlines()) == n_events
    audit_log.close()


def test_close_writes_what_is_queued_and_ignores_later_events(tmp_path):
    audit_log = EventAuditLog(tmp_path)
    audit_log.record(_SampleScanEvent(scan_id=uuid4()))

    audit_log.close()
    audit_log.record(_SampleScanEvent(scan_id=uuid4()))

    assert len(audit_log.path.read_text(encoding="utf-8").splitlines()) == 1
