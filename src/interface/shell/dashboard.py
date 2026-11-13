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
from interface.widgets.panels.inertial_probe_panel import InertialProbePanel
from interface.widgets.panels.hardware_advanced_config_panel import HardwareAdvancedConfigPanel
from interface.widgets.panels.calibration_panel import CalibrationPanel
from interface.widgets.panels.frequency_sweep_panel import FrequencySweepPanel
from interface.widgets.panels.external_modules_panel import ExternalModulesPanel
from interface.widgets.panels.measured_object_registry_panel import MeasuredObjectRegistryPanel
from interface.widgets.sensor_orientation_view.sensor_orientation_view import SensorOrientationView
from interface.widgets.panels.logs_panel import LogsPanel


class SettingsPanel(BasePanel):
    """Settings panel — global application preferences."""

    def __init__(self, parent=None, config_store: UIConfigStore = None):
        super().__init__("System Settings", "#607D8B", parent)
        self._config_store = config_store or UIConfigStore()

        # The motion referential (limit switches / centred) lives in the Motion Control panel, next to what
        # it changes; it used to be here, two panels away from the positions it rewrites.
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
            "aefi_voltage_map": ScanVisualizationPanel(),
            "aefi_voltage_profiles": ScanVisualizationPanel(profiles=True),
            # Field channel set depends on the connected probe (mono/bi/tri-axial):
            # left empty, populated lazily from the first scan point.
            "electric_field_map": ScanVisualizationPanel(channels=()),
            "electric_field_profiles": ScanVisualizationPanel(profiles=True, channels=()),
            "frequency_sweep": FrequencySweepPanel(),
            "measured_objects": MeasuredObjectRegistryPanel(),
            "aefi_continuous_reading": AefiContinuousReadingPanel(),
            "electric_field_probe": ElectricFieldProbePanel(),
            "inertial_probe": InertialProbePanel(),
            "motion": MotionPanelCompact(),
            "excitation": ExcitationPanel(),
            "hardware_config": HardwareAdvancedConfigPanel(),
            "calibration": CalibrationPanel(
                sensor_orientation_view=SensorOrientationView()
            ),
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
            # "Narda" = UI label for the electric field probe, for now (panel ids keep
            # the generic electric_field_* naming).
            "aefi_voltage_map": ("AEFI Voltage Map Plot", "Scan"),
            "aefi_voltage_profiles": ("AEFI Voltage Profiles Plot", "Scan"),
            "electric_field_map": ("Narda Map Plot", "Scan"),
            "electric_field_profiles": ("Narda Profiles Plot", "Scan"),
            "frequency_sweep": ("Frequency Sweep", "Scan"),
            "measured_objects": ("Objets mesurés", "Scan"),
            "aefi_continuous_reading": ("AEFI Continuous Reading", "Continuous Reading"),
            "electric_field_probe": ("Narda Continuous Reading", "Continuous Reading"),
            "inertial_probe": ("Capteur inertiel", "Continuous Reading"),
            "motion": ("Motion Control", "Hardware"),
            "excitation": ("Excitation & Lock-In Detection", "Hardware"),
            "hardware_config": ("Hardware Advanced Config", "Hardware"),
            "calibration": ("Calibration", "Hardware"),
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
