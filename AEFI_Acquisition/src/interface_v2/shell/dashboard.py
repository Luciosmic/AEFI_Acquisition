from PySide6.QtWidgets import QWidget, QVBoxLayout, QDockWidget
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
from interface_v2.widgets.panels.motion_panel import MotionPanel
from interface_v2.widgets.panels.excitation_panel import ExcitationPanel
from interface_v2.widgets.panels.continuous_acquisition_panel import ContinuousAcquisitionPanel
from interface_v2.widgets.panels.hardware_advanced_config_panel import HardwareAdvancedConfigPanel

from interface_v2.presenters.hardware_advanced_config_presenter import HardwareAdvancedConfigPresenter
from application.services.hardware_configuration_service.hardware_configuration_service import HardwareConfigurationService
from infrastructure.mocks.adapter_mock_i_hardware_advanced_configurator import MockHardwareAdvancedConfigurator

class SettingsPanel(BasePanel):
    """Placeholder for Settings panel."""
    def __init__(self, parent=None):
        super().__init__("System Settings", "#607D8B", parent)

class Dashboard(QWidget):
    """
    Composition Root for the Interface V2.
    Now uses WindowsCarrier as a widget (not inheritance).
    """
    
    # Layout file path
    LAYOUT_FILE = os.path.expanduser("~/.aefi_acquisition_layout.dat")
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AEFI Acquisition - Interface V2 (QtAds)")
        self.resize(1400, 900)
        
        # --- 1. Presentation Models (State) ---
        self.taskbar_model = TaskbarPresentationModel()
        self.carrier_model = CarrierPresentationModel()
        
        # --- 2. Widgets (Infrastructure) ---
        self.carrier_view = WindowsCarrier()  # Now a QWidget, not QMainWindow
        self.taskbar_view = ModernTaskbar()
        
        # --- 3. Widgets (Domain Panels) ---
        self.panels = {
            "scan_control": ScanControlPanel(),
            "scan_results": ScanVisualizationPanel(),
            "continuous": ContinuousAcquisitionPanel(),
            "motion": MotionPanel(),
            "excitation": ExcitationPanel(),
            "hardware_config": HardwareAdvancedConfigPanel(),
            "settings": SettingsPanel()
        }
        
        # Panel titles for docks
        self.panel_titles = {
            "scan_control": "Scan Control",
            "scan_results": "Scan Results",
            "continuous": "Continuous Acq.",
            "motion": "Motion Control",
            "excitation": "Excitation",
            "hardware_config": "Hardware Config",
            "settings": "Settings"
        }
        
        # Register panels as docks
        for pid, widget in self.panels.items():
            title = self.panel_titles.get(pid, pid)
            self.carrier_view.register_panel(pid, widget, title)
        
        # Restore layout or arrange default
        if not self.restore_layout():
            self.carrier_view.arrange_grid_layout()
        
        # --- 4. Presenters (Orchestration) ---
        self.taskbar_presenter = TaskbarPresenter(
            self.taskbar_model, 
            self.taskbar_view
        )
        
        # Hardware Advanced Config Presenter (with mocks)
        mock_configurator = MockHardwareAdvancedConfigurator()
        hardware_config_service = HardwareConfigurationService([mock_configurator])
        self.hardware_config_presenter = HardwareAdvancedConfigPresenter(hardware_config_service)
        self._wire_hardware_config()
        
        # --- 5. Data / Config (Bootstrap) ---
        # Register panels to Taskbar (Menu)
        self.taskbar_presenter.register_panel("scan_control", "Scan Control")
        self.taskbar_presenter.register_panel("scan_results", "Scan Results")
        self.taskbar_presenter.register_panel("continuous", "Continuous Acq.")
        self.taskbar_presenter.register_panel("motion", "Motion Control")
        self.taskbar_presenter.register_panel("excitation", "Excitation")
        self.taskbar_presenter.register_panel("hardware_config", "Hardware Config")
        self.taskbar_presenter.register_panel("settings", "Settings")
        
        # --- 6. Layout Composition ---
        self._setup_layout()

        # --- 7. Signal Wiring (Flow Control) ---
        
        # Flux: Taskbar Click -> Dashboard -> Toggle or Focus
        self.taskbar_presenter.panel_toggle_requested.connect(self.on_panel_toggle_requested)
        
        # Flux: Panel Visibility Changes -> Dashboard -> Taskbar Update
        for panel_id, dock in self.carrier_view._panels.items():
            # Connect each dock's visibility signal
            dock.viewToggled.connect(
                lambda visible, pid=panel_id: self.on_panel_visibility_changed(pid, visible)
            )
        
        # Don't sync visibility here - do it in showEvent after layout is fully applied
        self._initial_sync_done = False
    
    def _wire_hardware_config(self):
        """Wire hardware advanced config presenter and panel."""
        panel = self.panels["hardware_config"]
        
        # Presenter -> Panel (updates)
        self.hardware_config_presenter.hardware_list_updated.connect(panel.set_hardware_list)
        self.hardware_config_presenter.specs_loaded.connect(panel.set_parameter_specs)
        self.hardware_config_presenter.status_message.connect(panel.set_status_message)
        
        # Panel -> Presenter (user actions)
        panel.hardware_selected.connect(self.hardware_config_presenter.select_hardware)
        panel.apply_requested.connect(self.hardware_config_presenter.apply_configuration)
        
        # Initial load
        self.hardware_config_presenter.refresh_hardware_list()

    def showEvent(self, event):
        """Sync taskbar visibility after widget is shown and layout restored."""
        super().showEvent(event)
        
        if not self._initial_sync_done:
            # Now that widget is shown, sync taskbar with actual panel visibility
            for panel_id in self.panels.keys():
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
        
        # Simple toggle
        dock.toggleView(not dock.isVisible())

    def on_panel_visibility_changed(self, panel_id: str, visible: bool):
        """
        Handle panel visibility changes from QtAds.
        Syncs the Taskbar to reflect open/closed state.
        """
        self.taskbar_presenter.set_panel_visibility(panel_id, visible)
    
    # --- Layout Persistence ---
    
    def save_layout(self) -> bool:
        """
        Save current layout to file.
        Returns True if successful.
        """
        try:
            state = self.carrier_view.save_layout()
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.LAYOUT_FILE), exist_ok=True)
            
            with open(self.LAYOUT_FILE, 'wb') as f:
                f.write(state)
            
            print(f"Layout saved to {self.LAYOUT_FILE}")
            return True
        except Exception as e:
            print(f"Failed to save layout: {e}")
            return False
    
    def restore_layout(self) -> bool:
        """
        Restore layout from file.
        Returns True if successful.
        """
        try:
            if not os.path.exists(self.LAYOUT_FILE):
                return False
            
            with open(self.LAYOUT_FILE, 'rb') as f:
                state = f.read()
            
            self.carrier_view.restore_layout(state)
            print(f"Layout restored from {self.LAYOUT_FILE}")
            return True
        except Exception as e:
            print(f"Failed to restore layout: {e}")
            return False
    
    def closeEvent(self, event):
        """Auto-save layout on close."""
        self.save_layout()
        event.accept()
