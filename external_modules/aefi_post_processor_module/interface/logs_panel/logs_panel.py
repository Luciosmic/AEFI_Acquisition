"""
LogsPanel - Humble view of the journal: shows the lines it is given and reports the click on "open the journal file".
Its behaviour lives in logs_presenter (see logs_presenter_intention.md).
"""

from PySide6.QtCore import QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget


class LogsPanel(QWidget):
    open_log_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        self.location_label = QLabel("")
        header.addWidget(self.location_label, 1)
        open_button = QPushButton("Ouvrir le fichier journal")
        open_button.clicked.connect(self.open_log_requested.emit)
        header.addWidget(open_button)
        layout.addLayout(header)
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.text.setStyleSheet("font-family: Consolas, Menlo, monospace; font-size: 9pt;")
        layout.addWidget(self.text)

    def set_location(self, text: str) -> None:
        self.location_label.setText(text)

    def append_line(self, text: str, color: str) -> None:
        line_format = QTextCharFormat()
        line_format.setForeground(QColor(color))
        cursor = self.text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text + "\n", line_format)
        self.text.setTextCursor(cursor)

    def open_file(self, path: str) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))
