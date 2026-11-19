"""
AcquisitionParametersPanel - Humble view of the acquisition parameters: shows the title and the label/value rows it is given.
It reads nothing, writes nothing and has no control. Its behaviour lives in acquisition_parameters_presenter
(see acquisition_parameters_presenter_intention.md).
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFormLayout, QFrame, QLabel, QScrollArea, QVBoxLayout, QWidget


class AcquisitionParametersPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.title = QLabel("")
        self.title.setStyleSheet("font-weight: bold;")
        self.title.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.title)
        # The rows scroll when the dock is too small to hold them all, instead of being clipped.
        content = QWidget()
        self.form = QFormLayout(content)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

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
