import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from domain.shared_kernel.events.domain_event import DomainEvent
from infrastructure.events.event_ring_buffer import EventRingBuffer
from infrastructure.events.in_memory_event_bus import InMemoryEventBus


@dataclass(frozen=True)
class ScanStarted(DomainEvent):
    scan_id: UUID = None
    total_points: int = 0


@dataclass(frozen=True)
class PositionUpdated(DomainEvent):
    x: float = 0.0


def test_wildcard_subscription_records_type_and_scalar_summary():
    bus = InMemoryEventBus()
    buffer = EventRingBuffer()
    bus.subscribe("*", buffer.record)
    scan_id = uuid4()

    bus.publish("scanstarted", ScanStarted(scan_id=scan_id, total_points=12))

    (row,) = buffer.recent()
    assert row["event_type"] == "scanstarted"
    assert row["summary"]["total_points"] == 12
    assert row["summary"]["scan_id"] == str(scan_id)
    assert "occurred_on" in row


def test_high_frequency_types_are_excluded_by_default():
    buffer = EventRingBuffer()
    buffer.record(PositionUpdated(x=1.0))
    buffer.record(ScanStarted())

    assert [r["event_type"] for r in buffer.recent()] == ["scanstarted"]


def test_excluded_types_are_configurable():
    buffer = EventRingBuffer(excluded_event_types=["scanstarted"])
    buffer.record(PositionUpdated())
    buffer.record(ScanStarted())

    assert [r["event_type"] for r in buffer.recent()] == ["positionupdated"]


def test_maxlen_keeps_only_the_newest():
    buffer = EventRingBuffer(maxlen=3)
    for i in range(10):
        buffer.record(ScanStarted(total_points=i))

    assert [r["summary"]["total_points"] for r in buffer.recent()] == [7, 8, 9]


def test_filters_by_type_since_and_limit():
    buffer = EventRingBuffer(excluded_event_types=[])
    now = datetime.now(timezone.utc)
    buffer.record(ScanStarted(total_points=1, occurred_on=now - timedelta(hours=1)))
    buffer.record(PositionUpdated(occurred_on=now))
    buffer.record(ScanStarted(total_points=2, occurred_on=now))
    buffer.record(ScanStarted(total_points=3, occurred_on=now))

    assert len(buffer.recent(event_type="ScanStarted")) == 3
    recent = buffer.recent(event_type="scanstarted", since=now - timedelta(minutes=1))
    assert [r["summary"]["total_points"] for r in recent] == [2, 3]
    assert [r["summary"]["total_points"] for r in buffer.recent(event_type="scanstarted", limit=1)] == [3]


def test_concurrent_writers_and_reader_do_not_break():
    buffer = EventRingBuffer(maxlen=100)
    stop = threading.Event()
    errors = []

    def write():
        for i in range(2000):
            buffer.record(ScanStarted(total_points=i))

    def read():
        while not stop.is_set():
            stop.wait(0.001)  # a reader spinning without pause would starve the writers
            try:
                buffer.recent()
            except Exception as e:  # e.g. deque mutated during iteration
                errors.append(e)

    reader = threading.Thread(target=read)
    writers = [threading.Thread(target=write) for _ in range(4)]
    reader.start()
    for w in writers:
        w.start()
    for w in writers:
        w.join()
    stop.set()
    reader.join()

    assert errors == []
    assert len(buffer.recent(limit=1000)) == 100
