"""
WindowsCarrier - Qt Advanced Docking System
Uses PySide6-QtAds for professional docking features.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt, Signal
import PySide6QtAds as QtAds

class WindowsCarrier(QWidget):
    """
    Carrier using Qt Advanced Docking System.
    
    Features:
    - Advanced splits (H/V with smooth resizing)
    - Tab groups (drag between areas)
    - Float (detachable windows)
    - Persistence (save/restore layout)
    - Modern UI (VS Code-like)
    """
    panel_focused = Signal(str)  # panel_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create dock manager
        QtAds.CDockManager.setConfigFlag(QtAds.CDockManager.OpaqueSplitterResize, True)
        QtAds.CDockManager.setConfigFlag(QtAds.CDockManager.FocusHighlighting, True)
        QtAds.CDockManager.setConfigFlag(QtAds.CDockManager.AllTabsHaveCloseButton, True)  # Enable close
        QtAds.CDockManager.setConfigFlag(QtAds.CDockManager.DragPreviewIsDynamic, True)
        
        self.dock_manager = QtAds.CDockManager(self)
        layout.addWidget(self.dock_manager)
        
        # Registry: panel_id -> CDockWidget
        self._panels = {}
        
        # Styling
        self.setStyleSheet("""
            ads--CDockManager {
                background-color: #2A2A2A;
            }
            ads--CDockWidgetTab {
                background-color: #3A3A3A;
                border-color: #444;
                color: #DDD;
            }
            ads--CDockWidgetTab[activeTab="true"] {
                background-color: #2E7D32;
                color: white;
            }
            ads--CDockAreaWidget {
                background-color: #2A2A2A;
                border: 1px solid #444;
            }
        """)
    
    def register_panel(self, panel_id: str, widget: QWidget, title: str):
        """
        Register a panel as a CDockWidget.
        
        Args:
            panel_id: Unique identifier
            widget: Panel widget
            title: Dock title
        """
        if panel_id in self._panels:
            self.focus_panel(panel_id)
            return
        
        # Create dock widget
        dock = QtAds.CDockWidget(title)
        dock.setWidget(widget)
        
        # Add to dock manager (center by default, will arrange later)
        self.dock_manager.addDockWidget(QtAds.CenterDockWidgetArea, dock)
        
        self._panels[panel_id] = dock
        
        # Connect signals
        dock.viewToggled.connect(
            lambda visible: self._on_panel_visibility_changed(panel_id, visible)
        )
    
    def focus_panel(self, panel_id: str):
        """Raise and focus the specified panel."""
        if panel_id not in self._panels:
            return
        
        dock = self._panels[panel_id]
        dock.toggleView(True)  # Show if hidden
        dock.raise_()
        
        self.panel_focused.emit(panel_id)
    
    def _on_panel_visibility_changed(self, panel_id: str, visible: bool):
        """Handle panel visibility changes."""
        if visible:
            self.panel_focused.emit(panel_id)
    
    def arrange_default_layout(self):
        """
        Arrange panels in default layout (all tabbed in center).
        """
        # QtAds automatically tabs panels added to same area
        # All panels already added to CenterDockWidgetArea
        pass
    
    def arrange_grid_layout(self):
        """
        Grid layout: Scan on left, others on right stacked.
        """
        if len(self._panels) < 2:
            return
        
        panel_ids = list(self._panels.keys())
        
        # Simple approach: add first to left, others to right (auto-stack)
        if "scan_control" in self._panels:
            first_id = "scan_control"
        else:
            first_id = panel_ids[0]
        
        first_dock = self._panels[first_id]
        
        # Add first to left
        self.dock_manager.addDockWidget(QtAds.LeftDockWidgetArea, first_dock)
        
        # Add others to right
        for pid in panel_ids:
            if pid == first_id:
                continue
            
            dock = self._panels[pid]
            # Add to right (will auto-stack vertically)
            self.dock_manager.addDockWidget(QtAds.RightDockWidgetArea, dock)
    
    def arrange_columns_layout(self):
        """All panels side by side."""
        panel_ids = list(self._panels.keys())
        if len(panel_ids) < 2:
            return
        
        # Add first
        first_dock = self._panels[panel_ids[0]]
        self.dock_manager.addDockWidget(QtAds.CenterDockWidgetArea, first_dock)
        
        # Add others to right of previous
        for i in range(1, len(panel_ids)):
            dock = self._panels[panel_ids[i]]
            prev_dock = self._panels[panel_ids[i-1]]
            
            area = self.dock_manager.dockArea(prev_dock)
            self.dock_manager.addDockWidget(QtAds.RightDockWidgetArea, dock, area)
    
    def arrange_rows_layout(self):
        """All panels stacked vertically."""
        panel_ids = list(self._panels.keys())
        if len(panel_ids) < 2:
            return
        
        # Add first
        first_dock = self._panels[panel_ids[0]]
        self.dock_manager.addDockWidget(QtAds.CenterDockWidgetArea, first_dock)
        
        # Add others below previous
        for i in range(1, len(panel_ids)):
            dock = self._panels[panel_ids[i]]
            prev_dock = self._panels[panel_ids[i-1]]
            
            area = self.dock_manager.dockArea(prev_dock)
            self.dock_manager.addDockWidget(QtAds.BottomDockWidgetArea, dock, area)
    
    def save_layout(self) -> bytes:
        """Save current layout state."""
        return self.dock_manager.saveState()
    
    def restore_layout(self, state: bytes):
        """Restore layout from saved state."""
        self.dock_manager.restoreState(state)
