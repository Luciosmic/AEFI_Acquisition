"""Observability of the post-processor: batch sync outcome, log file, System Feedback forwarding."""

import logging
import os

import pytest

from aefi_post_processor_module import composition_root
from aefi_post_processor_module.logging_setup import FeedbackLogHandler, configure_logging


@pytest.fixture
def restore_root_logging():
    root = logging.getLogger()
    handlers, level = root.handlers[:], root.level
    yield
    for handler in root.handlers:
        if handler not in handlers:
            handler.close()
    root.handlers[:] = handlers
    root.setLevel(level)


class _FakePipeline:
    """Fails on any CSV whose folder name contains 'broken', succeeds otherwise."""

    def __init__(self, output_path):
        self.output_path = output_path

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def run_full_pipeline(self, csv_path, rotation_angles=None, reference_point=(0, 0)):
        if "broken" in csv_path.parent.name:
            raise ValueError("malformed CSV")
        self.output_path.write_text("h5", encoding="utf-8")


def _make_scan(raw_dir, name, with_h5=False):
    folder = raw_dir / name
    folder.mkdir()
    csv = folder / f"{name}_aefi.csv"
    csv.write_text("x,y\n", encoding="utf-8")
    if with_h5:
        h5 = folder / f"{name}.h5"
        h5.write_text("h5", encoding="utf-8")
        stamp = csv.stat().st_mtime
        os.utime(h5, (stamp + 10, stamp + 10))
    return folder


def test_sync_reports_each_scan_outcome_and_names_failures(tmp_path, monkeypatch, caplog):
    monkeypatch.setattr(composition_root, "ProcessingPipeline", _FakePipeline)
    monkeypatch.setattr(composition_root, "_ideal_rotation_angles", lambda: (35.3, 45.0, 0.0))
    _make_scan(tmp_path, "20261112_stepScan_ok")
    _make_scan(tmp_path, "20261112_stepScan_broken")
    _make_scan(tmp_path, "20261112_flyScan_done", with_h5=True)

    with caplog.at_level(logging.DEBUG):
        summary = composition_root.sync_scans(tmp_path)

    assert summary.processed == ["20261112_stepScan_ok"]
    assert summary.failed == ["20261112_stepScan_broken"]
    assert summary.skipped == ["20261112_flyScan_done"]

    messages = [r.getMessage() for r in caplog.records]
    assert any(
        m.startswith("scan.failed scan=20261112_stepScan_broken error_type=ValueError") for m in messages
    )
    assert any("rotation_origin=ideal_template" in m and "20261112_stepScan_ok" in m for m in messages)
    assert "scan.up_to_date scan=20261112_flyScan_done action=none" in messages
    finished = [r for r in caplog.records if r.getMessage().startswith("sync.finished")]
    assert finished[0].levelno == logging.WARNING
    assert "processed=1 skipped=1 failed=1" in finished[0].getMessage()


def test_sync_on_missing_directory_logs_an_error(tmp_path, caplog):
    summary = composition_root.sync_scans(tmp_path / "absent")

    assert summary.processed == summary.failed == summary.skipped == []
    assert any(r.levelno == logging.ERROR and "raw_dir_not_found" in r.getMessage() for r in caplog.records)


def test_feedback_replays_records_emitted_before_the_window_then_forwards_without_traceback():
    handler = FeedbackLogHandler()
    logger = logging.getLogger("aefi_post_processor_module.test_feedback")
    logger.propagate = False
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    received = []
    try:
        logger.info("sync.started scans_found=%d", 2)
        logger.debug("scan.up_to_date scan=a")  # below the handler level: not shown
        handler.attach(lambda levelno, message: received.append((levelno, message)))
        try:
            raise ValueError("boom")
        except ValueError:
            logger.exception("scan.failed scan=b")
    finally:
        logger.removeHandler(handler)

    assert received == [(logging.INFO, "sync.started scans_found=2"), (logging.ERROR, "scan.failed scan=b")]


def test_configure_logging_writes_the_run_to_its_file(tmp_path, restore_root_logging, monkeypatch):
    monkeypatch.delenv("AEFI_LOG_LEVEL", raising=False)
    log_file = tmp_path / "logs" / "post_processor.log"
    log_file.parent.mkdir()
    log_file.write_text("previous run\n", encoding="utf-8")

    feedback = configure_logging(log_file)
    logging.getLogger("aefi_post_processor_module.test").warning("scan.failed scan=c")
    for handler in logging.getLogger().handlers:
        handler.flush()

    content = log_file.read_text(encoding="utf-8")
    assert "previous run" not in content
    assert "WARNING aefi_post_processor_module.test: scan.failed scan=c" in content
    received = []
    feedback.attach(lambda levelno, message: received.append(message))
    assert "scan.failed scan=c" in received
