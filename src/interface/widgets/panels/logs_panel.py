import logging
import os
import sys

from PySide6.QtCore import QObject, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from interface.widgets.panels.base_panel import BasePanel

_WARNING_STYLE = "color: #FF9800; font-weight: bold;"


def _format_size(size_bytes: int) -> str:
    gb = size_bytes / 1024**3
    return f"{gb:.1f} Go".replace(".", ",") if gb >= 1 else f"{size_bytes / 1024**2:.0f} Mo"


def _format_date(utc_datetime) -> str:
    return utc_datetime.astimezone().strftime("%d/%m/%Y")


class LogsPanel(BasePanel):
    """Read-only scrollback of everything printed/logged since app launch,
    with a one-line event audit log size and a "Gérer" view (details, open
    the folder, delete old sessions). The size line stays hidden until a
    summary arrives — the splash's panel never gets one."""

    manage_requested = Signal()
    purge_requested = Signal()
    purge_confirmed = Signal()

    def __init__(self, parent=None):
        super().__init__("Logs", "#9E9E9E", parent)
        self.label.hide()  # the dashboard tab already names the panel; keep the room for the logs
        self._event_log_location = ""

        self.stack = QStackedWidget()
        self.layout.addWidget(self.stack)
        logs_page = QWidget()
        logs_layout = QVBoxLayout(logs_page)
        logs_layout.setContentsMargins(0, 0, 0, 0)
        self.stack.addWidget(logs_page)
        self.manage_page = self._build_manage_page()
        self.stack.addWidget(self.manage_page)

        self.event_log_row = QWidget()
        event_log_layout = QHBoxLayout(self.event_log_row)
        event_log_layout.setContentsMargins(0, 0, 0, 0)
        self.event_log_label = QLabel()
        event_log_layout.addWidget(self.event_log_label)
        manage_button = QPushButton("Gérer")
        manage_button.clicked.connect(self._open_manage_page)
        event_log_layout.addWidget(manage_button)
        event_log_layout.addStretch()
        self.event_log_row.setVisible(False)
        logs_layout.addWidget(self.event_log_row)

        level_row = QHBoxLayout()
        self.debug_checkbox = QCheckBox("Debug")
        self.debug_checkbox.toggled.connect(self._on_level_toggled)
        level_row.addWidget(self.debug_checkbox)
        self.warning_checkbox = QCheckBox("Warning only")
        self.warning_checkbox.toggled.connect(self._on_level_toggled)
        level_row.addWidget(self.warning_checkbox)
        level_row.addStretch()
        logs_layout.addLayout(level_row)
        # A panel built after install_console_capture (the dashboard's) reflects
        # the level already in force (e.g. AEFI_LOG_LEVEL=DEBUG) instead of showing unchecked.
        self.debug_checkbox.setChecked(logging.getLogger().getEffectiveLevel() == logging.DEBUG)

        self.text_edit = QPlainTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setMaximumBlockCount(5000)
        self.text_edit.setStyleSheet("font-family: Consolas, monospace; font-size: 11px;")
        logs_layout.addWidget(self.text_edit)

    def _build_manage_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Journal d'événements")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        explanation = QLabel(
            "Tous les événements de chaque lancement du logiciel, échantillons compris : un filet de "
            "sécurité pour retrouver après coup ce que le logiciel a réellement fait. Un fichier par "
            "lancement (« session »). Rien n'est supprimé automatiquement."
        )
        explanation.setWordWrap(True)
        layout.addWidget(explanation)

        form = QFormLayout()
        self.manage_size_label = QLabel()
        self.manage_sessions_label = QLabel()
        self.manage_oldest_label = QLabel()
        self.manage_location_label = QLabel()
        self.manage_location_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        form.addRow("Taille :", self.manage_size_label)
        form.addRow("Sessions :", self.manage_sessions_label)
        form.addRow("Plus ancienne :", self.manage_oldest_label)
        form.addRow("Dossier :", self.manage_location_label)
        layout.addLayout(form)

        buttons = QHBoxLayout()
        self.open_folder_button = QPushButton("Ouvrir le dossier")
        self.open_folder_button.clicked.connect(self._open_event_log_folder)
        buttons.addWidget(self.open_folder_button)
        self.purge_button = QPushButton()
        self.purge_button.clicked.connect(self.purge_requested)
        buttons.addWidget(self.purge_button)
        buttons.addStretch()
        back_button = QPushButton("Retour")
        back_button.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        buttons.addWidget(back_button)
        layout.addLayout(buttons)
        layout.addStretch()
        return page

    def _open_manage_page(self) -> None:
        self.stack.setCurrentWidget(self.manage_page)
        self.manage_requested.emit()  # fresh figures: the live session keeps growing

    def _open_event_log_folder(self) -> None:
        if self._event_log_location:
            QDesktopServices.openUrl(QUrl.fromLocalFile(self._event_log_location))

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
        size = _format_size(summary.total_size_bytes)
        warning_style = _WARNING_STYLE if summary.size_warning else ""
        self.event_log_label.setText(f"Journal d'événements : {size}")
        self.event_log_label.setStyleSheet(warning_style)
        if summary.size_warning:
            size += f" — au-delà de {_format_size(summary.size_warning_threshold_bytes)}"
        self.manage_size_label.setText(size)
        self.manage_size_label.setStyleSheet(warning_style)
        self.manage_sessions_label.setText(str(summary.session_count))
        self.manage_oldest_label.setText(
            _format_date(summary.oldest_started_at) if summary.oldest_started_at is not None else "—"
        )
        self._event_log_location = summary.location
        self.manage_location_label.setText(summary.location)

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
