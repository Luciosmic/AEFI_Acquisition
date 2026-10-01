import logging
import os
import sys

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QMessageBox, QPlainTextEdit, QPushButton, QWidget

from interface.widgets.panels.base_panel import BasePanel


def _format_size(size_bytes: int) -> str:
    gb = size_bytes / 1024**3
    return f"{gb:.1f} Go".replace(".", ",") if gb >= 1 else f"{size_bytes / 1024**2:.0f} Mo"


def _format_date(utc_datetime) -> str:
    return utc_datetime.astimezone().strftime("%d/%m/%Y")


class LogsPanel(BasePanel):
    """Read-only scrollback of everything printed/logged since app launch,
    plus the event audit log's size and the deletion of its old sessions
    (row hidden until a summary arrives — the splash's panel never gets one)."""

    purge_requested = Signal()
    purge_confirmed = Signal()

    def __init__(self, parent=None):
        super().__init__("Logs", "#9E9E9E", parent)
        self.label.hide()  # the dashboard tab already names the panel; keep the room for the logs

        self.event_log_row = QWidget()
        event_log_layout = QHBoxLayout(self.event_log_row)
        event_log_layout.setContentsMargins(0, 0, 0, 0)
        self.event_log_label = QLabel()
        event_log_layout.addWidget(self.event_log_label)
        event_log_layout.addStretch()
        self.purge_button = QPushButton()
        self.purge_button.clicked.connect(self.purge_requested)
        event_log_layout.addWidget(self.purge_button)
        self.event_log_row.setVisible(False)
        self.layout.addWidget(self.event_log_row)

        level_row = QHBoxLayout()
        self.debug_checkbox = QCheckBox("Debug")
        self.debug_checkbox.toggled.connect(self._on_level_toggled)
        level_row.addWidget(self.debug_checkbox)
        self.warning_checkbox = QCheckBox("Warning only")
        self.warning_checkbox.toggled.connect(self._on_level_toggled)
        level_row.addWidget(self.warning_checkbox)
        level_row.addStretch()
        self.layout.addLayout(level_row)
        # A panel built after install_console_capture (the dashboard's) reflects
        # the level already in force (e.g. AEFI_LOG_LEVEL=DEBUG) instead of showing unchecked.
        self.debug_checkbox.setChecked(logging.getLogger().getEffectiveLevel() == logging.DEBUG)

        self.text_edit = QPlainTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setMaximumBlockCount(5000)
        self.text_edit.setStyleSheet("font-family: Consolas, monospace; font-size: 11px;")
        self.layout.addWidget(self.text_edit)

    def _on_level_toggled(self) -> None:
        # Debug wins if both are checked — INFO (which already includes
        # WARNING/ERROR) is the default when neither is checked.
        if self.debug_checkbox.isChecked():
            level = logging.DEBUG
        elif self.warning_checkbox.isChecked():
            level = logging.WARNING
        else:
            level = logging.INFO
        logging.getLogger().setLevel(level)

    def set_event_log_summary(self, summary) -> None:
        """summary: EventLogSummaryDTO."""
        text = f"Journal d'événements : {_format_size(summary.total_size_bytes)} · {summary.session_count} session(s)"
        if summary.oldest_started_at is not None:
            text += f" · depuis le {_format_date(summary.oldest_started_at)}"
        if summary.size_warning:
            text += f" — au-delà de {_format_size(summary.size_warning_threshold_bytes)}"
        self.event_log_label.setText(text)
        self.event_log_label.setStyleSheet("color: #FF9800; font-weight: bold;" if summary.size_warning else "")
        self.event_log_label.setToolTip(
            "Fichiers .aefi_acquisition/logs/events/ : tous les événements de chaque lancement du logiciel "
            "(filet de sécurité). Rien n'est supprimé automatiquement."
        )

        self.purge_button.setText(f"Supprimer les sessions de plus de {summary.retention_days} jours…")
        self.purge_button.setEnabled(summary.expired_session_count > 0)
        self.purge_button.setToolTip(
            f"{summary.expired_session_count} session(s), {_format_size(summary.expired_size_bytes)}"
            if summary.expired_session_count
            else f"Aucune session de plus de {summary.retention_days} jours"
        )
        self.event_log_row.setVisible(True)

    def confirm_purge(self, summary) -> None:
        """summary: EventLogSummaryDTO with expired sessions to delete."""
        answer = QMessageBox.question(
            self,
            "Supprimer d'anciennes sessions",
            f"Supprimer définitivement {summary.expired_session_count} session(s) du journal d'événements "
            f"({_format_size(summary.expired_size_bytes)}), du {_format_date(summary.expired_oldest_started_at)} "
            f"au {_format_date(summary.expired_newest_started_at)} ?\n\n"
            f"Les sessions de moins de {summary.retention_days} jours, la session en cours et les fichiers "
            "des exports de scan ne sont pas touchés.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.purge_confirmed.emit()

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

    # AEFI_LOG_LEVEL=DEBUG / AEFI_LOG_FILE=<path>: headless-readable logs (e.g. for an agent
    # tailing a run) — the panel alone swallows stdout, so nothing is readable outside the UI.
    level = getattr(logging, os.environ.get("AEFI_LOG_LEVEL", "INFO").upper(), logging.INFO)
    panel_handler = logging.StreamHandler(stream)
    panel_handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
    handlers = [panel_handler]
    log_file = os.environ.get("AEFI_LOG_FILE")
    if log_file:
        file_handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")
        file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        handlers.append(file_handler)
    logging.basicConfig(handlers=handlers, level=level, force=True)
    logs_panel.debug_checkbox.setChecked(level == logging.DEBUG)

    return stream
