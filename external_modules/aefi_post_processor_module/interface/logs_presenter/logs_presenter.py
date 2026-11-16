"""
LogsPresenter - What the Logs panel shows and does (see logs_presenter_intention.md).
"""

import logging

logger = logging.getLogger(__name__)

_ERROR_COLOR = "#F44336"
_WARNING_COLOR = "#FF9800"
_DEFAULT_COLOR = "#CCCCCC"


class LogsPresenter:
    def __init__(self, view, log_file: str):
        self._view = view
        self._log_file = log_file
        view.set_location(f"Journal : {log_file}")
        view.open_log_requested.connect(self.on_open_log_requested)

    def append_feedback(self, levelno: int, message: str) -> None:
        """Sink of the FeedbackLogHandler: one log record per line, warnings and errors coloured."""
        if levelno >= logging.ERROR:
            color = _ERROR_COLOR
        elif levelno >= logging.WARNING:
            color = _WARNING_COLOR
        else:
            color = _DEFAULT_COLOR
        self._view.append_line(f"{logging.getLevelName(levelno)} {message}", color)

    def on_open_log_requested(self) -> None:
        logger.info("logs.open_requested file=%s", self._log_file)
        self._view.open_file(self._log_file)
