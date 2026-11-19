"""
AcquisitionParametersPanel - Humble view of the acquisition parameters: shows the title and the label/value rows it is given.
It reads nothing, writes nothing and has no control. Its behaviour lives in acquisition_parameters_presenter
(see acquisition_parameters_presenter_intention.md).
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFormLayout, QLabel, QVBoxLayout, QWidget


class AcquisitionParametersPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.title = QLabel("")
        self.title.setStyleSheet("font-weight: bold;")
        self.title.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.title)
        self.form = QFormLayout()
        layout.addLayout(self.form)
        layout.addStretch()

    def set_title(self, text: str) -> None:
        self.title.setText(text)

    def set_rows(self, rows) -> None:
        while self.form.rowCount():
            self.form.removeRow(0)
        for label, value in rows:
            shown = QLabel(value)
            shown.setWordWrap(True)
            shown.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self.form.addRow(QLabel(label), shown)
