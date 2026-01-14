from PySide6.QtWidgets import QWidget, QVBoxLayout, QDockWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
import os

from interface_v2.presentation.taskbar_model import TaskbarPresentationModel
from interface_v2.presentation.carrier_model import CarrierPresentationModel

from interface_v2.presenters.taskbar_presenter import TaskbarPresenter

from interface_v2.widgets.taskbar.modern_taskbar import ModernTaskbar
from interface_v2.widgets.carrier.windows_carrier import WindowsCarrier
from interface_v2.widgets.panels.base_panel import BasePanel
from interface_v2.widgets.panels.scan_control_panel import ScanControlPanel
from interface_v2.widgets.panels.scan_visualization_panel import ScanVisualizationPanel
from interface_v2.widgets.panels.motion_panel_compact import MotionPanelCompact
from interface_v2.widgets.panels.excitation_panel import ExcitationPanel
from interface_v2.widgets.panels.continuous_acquisition_panel import ContinuousAcquisitionPanel
from interface_v2.widgets.panels.hardware_advanced_config_panel import HardwareAdvancedConfigPanel
from interface_v2.widgets.panels.sensor_transformation_panel import SensorTransformationPanel



class SettingsPanel(BasePanel):
    """Placeholder for Settings panel."""
    def __init__(self, parent=None):
        super().__init__("System Settings", "#607D8B", parent)
        # Use self.layout from BasePanel instead of creating a new one
        self.layout.addWidget(QLabel("Global Application Settings"))
        self.layout.addStretch()

class Dashboard(QWidget):
    """
    Main Interface V2 Shell.
    """
    def __init__(self):
        super().__init__()
        
        # --- 1. Panel Instantiation ---

        self.panels = {
            "scan_control": ScanControlPanel(),
            "scan_viz": ScanVisualizationPanel(),
            "continuous": ContinuousAcquisitionPanel(),
            "motion": MotionPanelCompact(),
            "excitation": ExcitationPanel(),
            "hardware_config": HardwareAdvancedConfigPanel(),
            "transformation": SensorTransformationPanel(),
            "settings": SettingsPanel()
        }
        
        # --- 2. UI Composition ---

        self.setWindowTitle("EFI Imaging Bench V2")
        self.resize(1200, 800)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. Content Area (Carrier) - Added FIRST to be on TOP
        self.carrier_model = CarrierPresentationModel()
        self.carrier_view = WindowsCarrier() 
        main_layout.addWidget(self.carrier_view, 1) # Stretch 1 to take available space
        
        # Connect Carrier -> Dashboard (for Sync)
        self.carrier_view.panel_visibility_changed.connect(self.on_panel_visibility_changed)

        # 2. Taskbar - Added SECOND to be at BOTTOM
        self.taskbar_model = TaskbarPresentationModel()
        self.taskbar_view = ModernTaskbar()
        self.taskbar_presenter = TaskbarPresenter(self.taskbar_model, self.taskbar_view)
        
        # Register panels
        panel_metadata = {
            "scan_control": "Scan Control",
            "scan_viz": "Visualization",
            "continuous": "Continuous Acq.",
            "motion": "Motion Control",
            "excitation": "Excitation",
            "hardware_config": "Hardware Config",
            "transformation": "Ref. Transform",
            "settings": "Settings"
        }
        
        for pid, title in panel_metadata.items():
            self.taskbar_presenter.register_panel(pid, title)
            
        # Add taskbar at the bottom
        self.taskbar_view.setFixedHeight(60) # Ensure fixed height
        main_layout.addWidget(self.taskbar_view)

        # Connection Taskbar -> Carrier
        self.taskbar_presenter.panel_toggle_requested.connect(self.on_panel_toggle_requested)

        # Register panels to Carrier (Docks)
        for pid, title in panel_metadata.items():
            if pid in self.panels:
                widget = self.panels[pid]
                self.carrier_view.register_panel(pid, widget, title)
                
        self._initial_sync_done = False
        
        # Attempt to restore previous layout
        if not self.restore_layout():
            # If no layout saved, use default arrangement
            self.carrier_view.arrange_default_layout()


    def showEvent(self, event):
        """Sync taskbar visibility after widget is shown and layout restored."""
        super().showEvent(event)
        
        if not self._initial_sync_done:
            # Now that widget is shown, sync taskbar with actual panel visibility
            for panel_id in self.panels.keys():
                if panel_id in self.carrier_view._panels:
                    is_visible = self.carrier_view._panels[panel_id].isVisible()
                    self.taskbar_presenter.set_panel_visibility(panel_id, is_visible)
            
            self._initial_sync_done = True

    def _setup_layout(self):
        """Setup main layout with carrier and taskbar."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 1. Carrier takes main space
        layout.addWidget(self.carrier_view, 1)
        
        # 2. Taskbar at bottom
        self.taskbar_view.setFixedHeight(60)
        layout.addWidget(self.taskbar_view)

    def on_panel_toggle_requested(self, panel_id: str):
        """
        Handle panel toggle from taskbar.
        Toggle visibility: close if open, open if closed.
        """
        if panel_id not in self.carrier_view._panels:
            return
        
        dock = self.carrier_view._panels[panel_id]
        dock.toggleView(not dock.isVisible())

    def on_panel_visibility_changed(self, panel_id: str, visible: bool):
        """
        Handle panel visibility changes from QtAds.
        Syncs the Taskbar to reflect open/closed state.
        """
        self.taskbar_presenter.set_panel_visibility(panel_id, visible)
    
    # --- Layout Persistence ---
    
    LAYOUT_FILE = os.path.expanduser("~/.aefi_acquisition_layout.dat")
    
    def save_layout(self) -> bool:
        try:
            state = self.carrier_view.save_layout()
            os.makedirs(os.path.dirname(self.LAYOUT_FILE), exist_ok=True)
            with open(self.LAYOUT_FILE, 'wb') as f:
                f.write(state)
            return True
        except Exception:
            return False
            
    def restore_layout(self) -> bool:
        try:
            if not os.path.exists(self.LAYOUT_FILE):
                return False
            with open(self.LAYOUT_FILE, 'rb') as f:
                state = f.read()
            self.carrier_view.restore_layout(state)
            return True
        except Exception:
            return False
    
    def closeEvent(self, event):
        """Auto-save layout on close."""
        self.save_layout()
        event.accept()
