"""
Post-processor logging setup.

See logging_setup_intention.md.
"""

import logging
import os
from pathlib import Path
from typing import Callable, List, Optional, Tuple

LOG_LEVEL_ENV = "AEFI_LOG_LEVEL"
_FILE_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"

FeedbackSink = Callable[[int, str], None]


class FeedbackLogHandler(logging.Handler):
    """Forwards each record's level and message to the window's System Feedback.

    Records emitted before the window exists (the batch sync runs first) are kept
    and replayed when the sink is attached, so the operator sees the sync outcome.
    Only the message is forwarded: tracebacks go to the log file, not the panel.
    """

    def __init__(self, level: int = logging.INFO):
        super().__init__(level)
        self._sink: Optional[FeedbackSink] = None
        self._pending: List[Tuple[int, str]] = []

    def attach(self, sink: FeedbackSink) -> None:
        self._sink = sink
        pending, self._pending = self._pending, []
        for levelno, message in pending:
            sink(levelno, message)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = record.getMessage()
        except Exception:
            self.handleError(record)
            return
        if self._sink is None:
            self._pending.append((record.levelno, message))
        else:
            self._sink(record.levelno, message)


def configure_logging(log_file: Path) -> FeedbackLogHandler:
    """Route every module logger to `log_file` (rewritten at each run), the console,
    and a FeedbackLogHandler returned for the window to attach to.

    The level follows AEFI_LOG_LEVEL like the main application (INFO by default).
    The file is deliberately not taken from AEFI_LOG_FILE: the dashboard launches this
    process with its own environment, and reusing the variable would truncate the
    application's log file.
    """
    level = getattr(logging, os.environ.get(LOG_LEVEL_ENV, "INFO").upper(), logging.INFO)

    log_file = Path(log_file)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(_FILE_FORMAT))
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(_FILE_FORMAT))
    feedback_handler = FeedbackLogHandler()

    logging.basicConfig(handlers=[file_handler, console_handler, feedback_handler], level=level, force=True)
    logging.getLogger(__name__).info("logging.configured log_file=%s level=%s", log_file, logging.getLevelName(level))
    return feedback_handler
