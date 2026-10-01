from datetime import datetime, timezone

from application.services.event_log_maintenance_service.ports.i_event_log_storage_port import StoredEventLogSession
from infrastructure.events.fake.fake_event_log_storage import FakeEventLogStorage


def _session(name, day, live=False):
    return StoredEventLogSession(name, datetime(2026, 1, day, tzinfo=timezone.utc), 10, live)


def test_lists_by_start_and_reproduces_real_failure_modes():
    storage = FakeEventLogStorage([_session("b", 2), _session("a", 1), _session("live", 3, live=True)], locked=["b"])

    assert [s.name for s in storage.list_sessions()] == ["a", "b", "live"]
    assert storage.delete_session("a").is_success
    assert storage.delete_session("a").error.reason == "no such session"
    assert storage.delete_session("b").error.reason == "file in use"
    assert storage.delete_session("live").error.reason == "live session"
    assert [s.name for s in storage.list_sessions()] == ["b", "live"]
