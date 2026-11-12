"""
Collapsible Section

See collapsible_section_intention.md.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QToolButton, QVBoxLayout, QWidget


class CollapsibleSection(QWidget):
    """A titled block whose content folds away. Folded by default."""

    def __init__(self, title: str, parent=None, expanded: bool = False):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self.header = QToolButton()
        self.header.setText(title)
        self.header.setCheckable(True)
        self.header.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.header.setStyleSheet("QToolButton { border: none; font-weight: bold; text-align: left; }")
        self.header.toggled.connect(self._on_toggled)
        layout.addWidget(self.header)

        self._content = None
        self._layout = layout
        self.header.setChecked(expanded)
        self._on_toggled(expanded)

    def set_content_widget(self, widget: QWidget) -> None:
        self._content = widget
        widget.setVisible(self.header.isChecked())
        self._layout.addWidget(widget)

    def is_expanded(self) -> bool:
        return self.header.isChecked()

    def _on_toggled(self, expanded: bool) -> None:
        self.header.setArrowType(Qt.DownArrow if expanded else Qt.RightArrow)
        if self._content is not None:
            self._content.setVisible(expanded)
