from abc import ABC, abstractmethod
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal
from interface_v2.presentation.taskbar_model import TaskbarPresentationModel

class TaskbarWidget(QWidget):
    """
    Abstract interface for Taskbar implementations (Strategy Pattern).
    Decouples the logic (Model/Presenter) from the rendering (View).
    """
    # Emitted when a user interactions triggers a panel change request
    # Payload: panel_id (str)
    panel_clicked = Signal(str) 

    def __init__(self, parent=None):
        super().__init__(parent)

    @abstractmethod
    def render(self, model: TaskbarPresentationModel):
        """
        Pure rendering method.
        Updates the widget state to match the PresentationModel.
        Must be idempotent.
        """
        pass
