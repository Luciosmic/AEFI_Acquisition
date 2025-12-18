from PySide6.QtWidgets import QBoxLayout, QPushButton, QFrame, QHBoxLayout
from PySide6.QtCore import Qt, QSize
from interface.widgets.taskbar.taskbar_widget import TaskbarWidget
from interface.presentation.taskbar_model import TaskbarPresentationModel

class ModernTaskbar(TaskbarWidget):
    """
    Modern implementation of the Taskbar.
    Uses CSS styling, flat design, and animations (conceptually).
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Layout
        self.layout_container = QHBoxLayout(self)
        self.layout_container.setContentsMargins(10, 5, 10, 5)
        self.layout_container.setSpacing(15)
        self.layout_container.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # State tracking for diffing
        self.buttons = {} # id -> QPushButton

        # Styling
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("""
            ModernTaskbar {
                background-color: #2D2D2D;
                border-top: 1px solid #3E3E3E;
                min-height: 60px;
            }
            QPushButton {
                background-color: transparent;
                color: #AAAAAA;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #383838;
                color: #FFFFFF;
            }
            QPushButton[active="true"] {
                background-color: #404040;
                color: #4CAF50; /* Green Accent */
                border-bottom: 2px solid #4CAF50;
            }
        """)

    def render(self, model: TaskbarPresentationModel):
        """
        Syncs the view with the model.
        Highlights all visible/open panels.
        """
        current_ids = set()

        # 1. Create or Update buttons
        for panel in model.panels:
            current_ids.add(panel.id)
            
            if panel.id not in self.buttons:
                # Create new button
                btn = QPushButton(panel.label)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                # Connect click signal
                # Closure capture fix: use default arg
                btn.clicked.connect(lambda checked, pid=panel.id: self.panel_clicked.emit(pid))
                
                self.layout_container.addWidget(btn)
                self.buttons[panel.id] = btn
            
            # Update state
            btn = self.buttons[panel.id]
            btn.setText(panel.label)
            
            # Update visibility styling
            # Highlight = panel is visible/open, not just active
            was_active = btn.property("active")
            is_visible = panel.is_visible
            
            if was_active != is_visible:
                btn.setProperty("active", is_visible)
                # Force re-polish to apply style
                btn.style().unpolish(btn)
                btn.style().polish(btn)

        # 2. Remove stale buttons
        all_known_ids = list(self.buttons.keys())
        for bid in all_known_ids:
            if bid not in current_ids:
                btn = self.buttons.pop(bid)
                self.layout_container.removeWidget(btn)
                btn.deleteLater()
