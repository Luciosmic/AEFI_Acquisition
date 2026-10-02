"""
Calibration Panel

Composite dock grouping every calibration type in one place (user request:
one panel for all calibrations, not one dock per type). Pure composition —
no logic, no signals of its own: dashboard_wiring.py connects directly to
the sub-widgets exposed as attributes.
"""

from typing import Dict, Optional

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from interface.widgets.panels.sensor_calibration_panel import SensorCalibrationPanel
from interface.widgets.panels.source_geometry_calibration_panel import SourceGeometryCalibrationPanel
from interface.widgets.panels.hardware_component_panel import HardwareComponentPanel
from interface.widgets.panels.acquisition_throughput_characterization_widget import (
    AcquisitionThroughputCharacterizationWidget,
)
from interface.widgets.panels.adc_output_rate_characterization_widget import AdcOutputRateCharacterizationWidget

_MICROCONTROLLER_KEY = "microcontroller"  # HardwareComponentKindDTO.key
_ADC_KEY = "adc"


class CalibrationPanel(QWidget):
    """Tabbed dock hosting every calibration sub-panel."""

    def __init__(self, parent=None, sensor_orientation_view: Optional[QWidget] = None):
        super().__init__(parent)

        self.sensor_calibration_panel = SensorCalibrationPanel(orientation_view=sensor_orientation_view)
        self.source_geometry_panel = SourceGeometryCalibrationPanel()
        self.hardware_component_panels: Dict[str, HardwareComponentPanel] = {}
        # Shown in the microcontroller tab, which it characterizes.
        self.acquisition_throughput_widget = AcquisitionThroughputCharacterizationWidget()
        # Shown in the ADC tab: ODR measured on DRDY at the oscilloscope.
        self.adc_output_rate_widget = AdcOutputRateCharacterizationWidget()

        self._tabs = QTabWidget()
        self._tabs.setUsesScrollButtons(True)
        self._tabs.addTab(self.sensor_calibration_panel, "Calibration capteur")
        self._tabs.addTab(self.source_geometry_panel, "Géométrie source")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._tabs)

    def add_hardware_component_tab(self, kind) -> HardwareComponentPanel:
        """One tab per hardware component kind (`HardwareComponentKindDTO`),
        added at wiring time since the kinds come from the application layer."""
        panel = HardwareComponentPanel(kind)
        if kind.key == _MICROCONTROLLER_KEY:
            panel.add_tool(self.acquisition_throughput_widget)
        if kind.key == _ADC_KEY:
            panel.add_tool(self.adc_output_rate_widget)
        self.hardware_component_panels[kind.key] = panel
        self._tabs.addTab(panel, kind.label)
        return panel
