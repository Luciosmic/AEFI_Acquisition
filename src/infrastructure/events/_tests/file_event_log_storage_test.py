import sys
from datetime import datetime, timezone

import pytest

from infrastructure.events.file_event_log_storage import FileEventLogStorage

OLD = "events_20260731T125327Z_2c8a78.jsonl"
LIVE = "events_20261001T122016Z_c7ea0e.jsonl"


@pytest.fixture
def log_dir(tmp_path):
    (tmp_path / OLD).write_text("x" * 10, encoding="utf-8")
    (tmp_path / "debug.log").write_text("not a session", encoding="utf-8")
    (tmp_path / "events_notadate_abcdef.jsonl").write_text("not a session", encoding="utf-8")
    return tmp_path


def test_lists_sessions_with_start_from_name_and_live_flag_even_before_live_file_exists(log_dir):
    storage = FileEventLogStorage(log_dir, live_session=log_dir / LIVE)

    sessions = storage.list_sessions()
    assert [(s.name, s.size_bytes, s.is_live) for s in sessions] == [(OLD, 10, False)]
    assert sessions[0].started_at == datetime(2026, 7, 31, 12, 53, 27, tzinfo=timezone.utc)

    (log_dir / LIVE).write_text("y", encoding="utf-8")
    assert [(s.name, s.is_live) for s in storage.list_sessions()] == [(OLD, False), (LIVE, True)]


def test_deletes_a_session_but_never_the_live_one_nor_foreign_files(log_dir):
    (log_dir / LIVE).write_text("y", encoding="utf-8")
    storage = FileEventLogStorage(log_dir, live_session=log_dir / LIVE)

    assert storage.delete_session(OLD).is_success
    assert not (log_dir / OLD).exists()
    assert storage.delete_session(OLD).is_failure  # already gone
    assert storage.delete_session(LIVE).is_failure
    assert storage.delete_session("debug.log").is_failure
    assert storage.delete_session("../" + LIVE).is_failure
    assert (log_dir / LIVE).exists() and (log_dir / "debug.log").exists()


@pytest.mark.skipif(sys.platform != "win32", reason="Windows refuses to delete an open file")
def test_file_open_elsewhere_is_reported_not_raised(log_dir):
    storage = FileEventLogStorage(log_dir, live_session=log_dir / LIVE)

    with (log_dir / OLD).open("a", encoding="utf-8"):
        result = storage.delete_session(OLD)

    assert result.is_failure
    assert (log_dir / OLD).exists()
