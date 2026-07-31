from PySide6.QtWidgets import QWidget, QVBoxLayout, QDockWidget, QHBoxLayout, QLabel, QGroupBox, QComboBox
from PySide6.QtCore import Qt, Signal
import os

from interface.logic.ui_config_store import UIConfigStore

from interface.presentation.taskbar_model import TaskbarPresentationModel
from interface.presentation.carrier_model import CarrierPresentationModel

from interface.presenters.taskbar_presenter import TaskbarPresenter

from interface.widgets.taskbar.modern_taskbar import ModernTaskbar
from interface.widgets.carrier.windows_carrier import WindowsCarrier
from interface.widgets.panels.base_panel import BasePanel
from interface.widgets.panels.scan_control_panel import ScanControlPanel
from interface.widgets.panels.scan_visualization_panel import ScanVisualizationPanel
from interface.widgets.panels.motion_panel_compact import MotionPanelCompact
from interface.widgets.panels.excitation_panel import ExcitationPanel
from interface.widgets.panels.aefi_continuous_reading_panel import AefiContinuousReadingPanel
from interface.widgets.panels.electric_field_probe_panel import ElectricFieldProbePanel
from interface.widgets.panels.hardware_advanced_config_panel import HardwareAdvancedConfigPanel
from interface.widgets.panels.sensor_transformation_panel import SensorTransformationPanel
from interface.widgets.panels.external_modules_panel import ExternalModulesPanel
from interface.widgets.panels.logs_panel import LogsPanel


class SettingsPanel(BasePanel):
    """Settings panel — global application preferences."""

    # (persisted key, display label)
    MOTION_REFERENTIAL_MODES = (
        ("limit_switch", "Limit switch (fins de course)"),
        ("centered", "Centered (0,0 = center, 4 quadrants)"),
    )

    motion_referential_changed = Signal(str)  # 'limit_switch' or 'centered'

    def __init__(self, parent=None, config_store: UIConfigStore = None):
        super().__init__("System Settings", "#607D8B", parent)
        self._config_store = config_store or UIConfigStore()

        motion_group = QGroupBox("Motion Referential")
        motion_layout = QVBoxLayout(motion_group)
        self.combo_referential = QComboBox()
        for _, label in self.MOTION_REFERENTIAL_MODES:
            self.combo_referential.addItem(label)
        saved_mode = self._config_store.load_motion_config().get("referential_mode", "limit_switch")
        saved_index = next((i for i, (key, _) in enumerate(self.MOTION_REFERENTIAL_MODES) if key == saved_mode), 0)
        self.combo_referential.setCurrentIndex(saved_index)
        self.combo_referential.currentIndexChanged.connect(self._on_referential_changed)
        motion_layout.addWidget(self.combo_referential)

        # Use self.layout from BasePanel instead of creating a new one
        self.layout.addWidget(motion_group)
        self.layout.addWidget(QLabel("Global Application Settings"))
        self.layout.addStretch()

    def _on_referential_changed(self, index: int):
        mode = self.MOTION_REFERENTIAL_MODES[index][0]
        self.motion_referential_changed.emit(mode)

    def get_current_referential_mode(self) -> str:
        return self.MOTION_REFERENTIAL_MODES[self.combo_referential.currentIndex()][0]

class Dashboard(QWidget):
    """
    Main Interface V2 Shell.
    """
    def __init__(self):
        super().__init__()

        # --- 1. Panel Instantiation ---

        self.panels = {
            "scan_control": ScanControlPanel(),
            "aefi_voltage_map": ScanVisualizationPanel(),
            "electric_field_map": ScanVisualizationPanel(enable_grid_view=False),
            "aefi_continuous_reading": AefiContinuousReadingPanel(),
            "electric_field_probe": ElectricFieldProbePanel(),
            "motion": MotionPanelCompact(),
            "excitation": ExcitationPanel(),
            "hardware_config": HardwareAdvancedConfigPanel(),
            "transformation": SensorTransformationPanel(),
            "external_modules": ExternalModulesPanel(),
            "logs": LogsPanel(),
            "settings": SettingsPanel()
        }
        
        # --- 2. UI Composition ---

        self.setWindowTitle("AEFI Acquisition Software")
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
        
        # Register panels — (label, group). Group order here also drives the taskbar's visual grouping.
        # external_modules is excluded below: it isn't a dock to toggle, it gets its own
        # standalone launcher dropdown (see add_action_group call further down).
        panel_metadata = {
            "scan_control": ("Scan Configuration", "Scan"),
            "aefi_voltage_map": ("AEFI Voltage Map", "Scan"),
            "electric_field_map": ("Electric Field Map", "Scan"),
            "aefi_continuous_reading": ("AEFI Continuous Reading", "Continuous Reading"),
            "electric_field_probe": ("Electric Field Continuous Reading", "Continuous Reading"),
            "motion": ("Motion Control", "Hardware"),
            "excitation": ("Excitation", "Hardware"),
            "hardware_config": ("Hardware Advanced Config", "Hardware"),
            "transformation": ("Sensor Transformation", "Hardware"),
            "external_modules": ("External Modules", "Système"),
            "logs": ("Logs", "Système"),
            "settings": ("Settings", "Système"),
        }

        for pid, (title, group) in panel_metadata.items():
            if pid == "external_modules":
                continue
            self.taskbar_presenter.register_panel(pid, title, group=group)

        # External Modules: its own standalone dropdown, listing the actual external
        # modules — clicking one launches it directly (QProcess), no dock to toggle.
        self.taskbar_view.add_action_group(
            "External Modules",
            [(key, label) for key, label, *_ in ExternalModulesPanel._LAUNCHERS],
            self._launch_external_module,
        )

        # Add taskbar at the bottom
        self.taskbar_view.setFixedHeight(60) # Ensure fixed height
        main_layout.addWidget(self.taskbar_view)

        # Connection Taskbar -> Carrier
        self.taskbar_presenter.panel_toggle_requested.connect(self.on_panel_toggle_requested)

        # Register panels to Carrier (Docks)
        for pid, (title, _group) in panel_metadata.items():
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

    def _launch_external_module(self, key: str):
        """Launch an external module (see ExternalModulesPanel._LAUNCHERS) from the taskbar dropdown."""
        self.panels["external_modules"].launch(key)

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
