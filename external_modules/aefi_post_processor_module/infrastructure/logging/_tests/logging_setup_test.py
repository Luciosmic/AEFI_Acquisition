"""Journal du post-traitement : fichier du lancement et transmission au cadre System Feedback."""

import logging

import pytest

from aefi_post_processor_module.infrastructure.logging.logging_setup import FeedbackLogHandler, configure_logging


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
