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
