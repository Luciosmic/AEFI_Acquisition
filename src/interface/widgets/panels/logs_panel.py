import logging
import sys

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QPlainTextEdit

from interface.widgets.panels.base_panel import BasePanel


class LogsPanel(BasePanel):
    """Read-only scrollback of everything printed/logged since app launch."""

    def __init__(self, parent=None):
        super().__init__("Logs", "#9E9E9E", parent)

        self.text_edit = QPlainTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setMaximumBlockCount(5000)
        self.text_edit.setStyleSheet("font-family: Consolas, monospace; font-size: 11px;")
        self.layout.addWidget(self.text_edit)

    def append_line(self, text: str) -> None:
        text = text.rstrip("\n")
        if text:
            self.text_edit.appendPlainText(text)


class EmittingStream(QObject):
    """File-like object that forwards writes as a thread-safe Qt signal."""

    text_written = Signal(str)

    def write(self, message: str) -> None:
        if message:
            self.text_written.emit(message)

    def flush(self) -> None:
        pass


def install_console_capture(logs_panel: LogsPanel) -> EmittingStream:
    """Redirect stdout/stderr and the root logger into logs_panel.

    Returns the EmittingStream so callers can connect additional widgets
    (e.g. a second, permanent logs panel) to the same text_written signal.

    ponytail: one stream captures every existing print() and logger.* call
    app-wide instead of editing each call site individually.
    """
    stream = EmittingStream()
    stream.text_written.connect(logs_panel.append_line)

    sys.stdout = stream
    sys.stderr = stream

    logging.basicConfig(
        stream=stream,
        level=logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
        force=True,
    )

    return stream
