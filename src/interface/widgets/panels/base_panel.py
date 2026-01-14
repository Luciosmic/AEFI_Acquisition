from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

class BasePanel(QWidget):
    """
    Base class for application panels.
    Purely for visual verification in this MVP.
    """
    def __init__(self, title: str, color: str, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        
        self.label = QLabel(title)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color}; border: 2px dashed {color}; border-radius: 10px;")
        
        self.layout.addWidget(self.label)
