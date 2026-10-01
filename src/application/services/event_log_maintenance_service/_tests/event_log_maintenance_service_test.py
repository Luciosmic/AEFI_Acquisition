"""EventLogMaintenanceService against FakeEventLogStorage, with a fixed clock."""

from datetime import datetime, timedelta, timezone

from application.services.event_log_maintenance_service.event_log_maintenance_service import (
    EventLogMaintenanceService,
    SIZE_WARNING_BYTES,
)
from application.services.event_log_maintenance_service.ports.i_event_log_storage_port import StoredEventLogSession
from infrastructure.events.fake.fake_event_log_storage import FakeEventLogStorage

NOW = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)
MB = 1024 * 1024


def _session(name, days_ago, size=MB, live=False):
    return StoredEventLogSession(name, NOW - timedelta(days=days_ago), size, live)


def _service(*sessions, locked=()):
    storage = FakeEventLogStorage(sessions, locked=locked)
    return EventLogMaintenanceService(storage, now=lambda: NOW), storage


def test_summary_previews_only_sessions_older_than_90_days():
    service, _ = _service(
        _session("old", 120, size=3 * MB),
        _session("older", 200, size=2 * MB),
        _session("just_under", 89),
        _session("live", 0, live=True),
    )

    summary = service.get_summary()

    assert summary.session_count == 4
    assert summary.total_size_bytes == 7 * MB
    assert summary.oldest_started_at == NOW - timedelta(days=200)
    assert not summary.size_warning
    assert summary.expired_session_count == 2
    assert summary.expired_size_bytes == 5 * MB
    assert summary.expired_oldest_started_at == NOW - timedelta(days=200)
    assert summary.expired_newest_started_at == NOW - timedelta(days=120)


def test_size_warning_from_20_gb():
    service, _ = _service(_session("big", 1, size=SIZE_WARNING_BYTES))

    assert service.get_summary().size_warning


def test_delete_removes_expired_sessions_and_keeps_recent_and_live():
    service, storage = _service(
        _session("old", 120, size=3 * MB),
        _session("recent", 10),
        _session("live_but_old_clock", 400, live=True),
    )

    result = service.delete_expired_sessions()

    assert result.deleted_session_count == 1
    assert result.freed_bytes == 3 * MB
    assert result.not_deleted == ()
    assert set(storage.sessions) == {"recent", "live_but_old_clock"}


def test_locked_session_is_reported_not_fatal():
    service, storage = _service(_session("locked", 120), _session("old", 130, size=2 * MB), locked=["locked"])

    result = service.delete_expired_sessions()

    assert result.deleted_session_count == 1
    assert result.freed_bytes == 2 * MB
    assert result.not_deleted == ("locked",)
    assert set(storage.sessions) == {"locked"}


def test_nothing_expired_deletes_nothing():
    service, storage = _service(_session("recent", 5))

    result = service.delete_expired_sessions()

    assert (result.deleted_session_count, result.freed_bytes, result.not_deleted) == (0, 0, ())
    assert set(storage.sessions) == {"recent"}
