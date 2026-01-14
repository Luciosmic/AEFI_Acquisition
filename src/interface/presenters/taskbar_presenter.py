from PySide6.QtCore import QObject, Slot, Signal
from interface.presentation.taskbar_model import TaskbarPresentationModel
from interface.widgets.taskbar.taskbar_widget import TaskbarWidget

class TaskbarPresenter(QObject):
    """
    Presenter for the Taskbar.
    - Synchronizes Domain Events -> Presentation Model.
    - Synchronizes View Events -> Domain Commands (via Signals).
    """
    # Signal emitted when user clicks a panel button
    panel_toggle_requested = Signal(str)  # panel_id

    def __init__(self, model: TaskbarPresentationModel, view: TaskbarWidget):
        super().__init__()
        self.model = model
        self.view = view
        
        # Connect View -> Presenter
        self.view.panel_clicked.connect(self.on_panel_clicked)
        
        # Initial Render
        self.view.render(self.model)

    @Slot(str)
    def on_panel_clicked(self, panel_id: str):
        """
        Handle user interaction from the View.
        Clicking toggles panel visibility or focuses it.
        """
        # Notify application layer (Dashboard will handle logic)
        self.panel_toggle_requested.emit(panel_id)

    # --- API called by Domain/Application Layer ---

    def register_panel(self, panel_id: str, label: str, icon: str = None):
        """
        Registers a new panel available in the application.
        """
        self.model.add_panel(panel_id, label, icon)
        self.view.render(self.model)

    def set_panel_visibility(self, panel_id: str, visible: bool):
        """
        Updates panel visibility state (called when panel shown/hidden).
        """
        if self.model.set_panel_visibility(panel_id, visible):
            self.view.render(self.model)
