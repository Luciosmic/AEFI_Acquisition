import threading
from dataclasses import dataclass, field

import pytest

from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.unit_of_work.in_memory_unit_of_work import InMemoryUnitOfWork


@dataclass
class SomethingHappened:
    n: int


@dataclass
class Aggregate:
    _events: list = field(default_factory=list)

    @property
    def domain_events(self):
        events, self._events = list(self._events), []
        return events


def _setup():
    bus = InMemoryEventBus()
    received = []
    bus.subscribe("somethinghappened", received.append)
    return bus, InMemoryUnitOfWork(bus), received


def test_events_published_only_after_commit():
    bus, uow, received = _setup()
    agg = Aggregate([SomethingHappened(1)])
    with uow:
        uow.register(agg)
        assert received == []
        uow.commit()
    assert received == [SomethingHappened(1)]


def test_no_event_on_exception():
    bus, uow, received = _setup()
    with pytest.raises(RuntimeError):
        with uow:
            uow.register(Aggregate([SomethingHappened(1)]))
            raise RuntimeError("boom")
    assert received == []


def test_no_event_without_commit():
    bus, uow, received = _setup()
    with uow:
        uow.register(Aggregate([SomethingHappened(1)]))
    assert received == []


def test_handler_can_open_second_uow_during_publication():
    bus, uow, received = _setup()
    second = Aggregate([SomethingHappened(2)])

    def handler(event):
        if event.n == 1:
            with uow:
                uow.register(second)
                uow.commit()

    bus.subscribe("somethinghappened", handler)
    with uow:
        uow.register(Aggregate([SomethingHappened(1)]))
        uow.commit()
    assert received == [SomethingHappened(1), SomethingHappened(2)]


def _wildcard(bus):
    seen = []
    bus.subscribe("*", lambda e: seen.append(e.n))
    return seen


def _commit(uow, *ns):
    with uow:
        uow.register(Aggregate([SomethingHappened(n) for n in ns]))
        uow.commit()


def test_event_committed_by_a_handler_is_delivered_after_the_event_being_delivered():
    bus, uow, _ = _setup()
    bus.subscribe("somethinghappened", lambda e: _commit(uow, 2) if e.n == 1 else None)
    seen = _wildcard(bus)  # "*" is dispatched after the typed handlers: it used to see 2 before 1

    _commit(uow, 1)

    assert seen == [1, 2]


def test_nested_commits_are_delivered_in_fifo_order_on_two_levels():
    bus, uow, received = _setup()
    other = InMemoryUnitOfWork(bus)  # another instance on the same thread shares the queue
    reactions = {1: 2, 2: 3}
    bus.subscribe("somethinghappened", lambda e: _commit(other, reactions[e.n]) if e.n in reactions else None)
    seen = _wildcard(bus)

    _commit(uow, 1, 10)

    # 1 and 10 were committed together: 2 (reaction to 1) waits behind 10, 3 behind 2.
    assert seen == [1, 10, 2, 3]
    assert [e.n for e in received] == [1, 10, 2, 3]


def test_a_failing_handler_does_not_stop_the_queue_nor_the_next_commits():
    bus, uow, _ = _setup()

    def handler(event):
        if event.n == 1:
            _commit(uow, 2)
            raise RuntimeError("handler boom")  # swallowed and logged by the bus

    bus.subscribe("somethinghappened", handler)
    seen = _wildcard(bus)

    _commit(uow, 1)
    _commit(uow, 5)

    assert seen == [1, 2, 5]


def test_dispatch_state_is_reset_when_the_delivery_raises():
    bus, uow, received = _setup()
    real_publish = bus.publish
    calls = []

    def publish_failing_once(topic, event):
        calls.append(event.n)
        if len(calls) == 1:
            raise RuntimeError("bus boom")
        real_publish(topic, event)

    bus.publish = publish_failing_once
    with pytest.raises(RuntimeError, match="bus boom"):
        _commit(uow, 1, 2)

    _commit(uow, 3)  # a stale queue would swallow it without delivering it

    assert [e.n for e in received] == [3]


def test_two_threads_dispatching_at_the_same_time_do_not_share_the_queue():
    bus = InMemoryEventBus()
    both_dispatching = threading.Barrier(2, timeout=5)
    delivered = []  # (thread name, n)
    lock = threading.Lock()

    def handler(event):
        if event.n in (1, 10):
            both_dispatching.wait()  # both threads are inside their own dispatch here
            _commit(InMemoryUnitOfWork(bus), event.n + 1)

    def record(event):
        with lock:
            delivered.append((threading.current_thread().name, event.n))

    bus.subscribe("somethinghappened", handler)
    bus.subscribe("*", record)
    threads = [threading.Thread(target=_commit, args=(InMemoryUnitOfWork(bus), n), name=f"t{n}") for n in (1, 10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    assert [n for name, n in delivered if name == "t1"] == [1, 2]
    assert [n for name, n in delivered if name == "t10"] == [10, 11]
