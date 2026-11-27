"""
Calibration Panel

Composite dock grouping every calibration and characterization measurement
in one place (user request: one panel for all calibrations, not one dock per
type). The component catalog — declaring, characterizing and mounting the
bench's components — is the bench configuration, in its own panel
(BenchConfigurationPanel): the two contexts are not mixed. Pure composition —
no logic, no signals of its own: dashboard_wiring.py connects directly to
the sub-widgets exposed as attributes.
"""

from typing import Optional

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from interface.widgets.panels.sensor_calibration_panel import SensorCalibrationPanel
from interface.widgets.panels.source_geometry_calibration_panel import SourceGeometryCalibrationPanel
from interface.widgets.panels.mechanical_transmission_panel import MechanicalTransmissionPanel
from interface.widgets.panels.acquisition_throughput_characterization_widget import (
    AcquisitionThroughputCharacterizationWidget,
)
from interface.widgets.panels.adc_output_rate_characterization_widget import AdcOutputRateCharacterizationWidget

# Thesis graph name of the ADC + DDS + microcontroller unit, whose
# measurements are grouped here as their catalog tabs are in the configuration.
_CONVERSION_UNIT_LABEL = "Unité de conversion entre signaux numériques et analogiques"


class CalibrationPanel(QWidget):
    """Tabbed dock hosting every calibration sub-panel."""

    def __init__(self, parent=None, sensor_orientation_view: Optional[QWidget] = None):
        super().__init__(parent)

        self.sensor_calibration_panel = SensorCalibrationPanel(orientation_view=sensor_orientation_view)
        self.source_geometry_panel = SourceGeometryCalibrationPanel()
        self.mechanical_transmission_panel = MechanicalTransmissionPanel()
        # Measured here; the values prefill the microcontroller / ADC forms of
        # the configuration panel, where the operator records them.
        self.acquisition_throughput_widget = AcquisitionThroughputCharacterizationWidget()
        self.adc_output_rate_widget = AdcOutputRateCharacterizationWidget()

        self._tabs = QTabWidget()
        self._tabs.setUsesScrollButtons(True)
        self._tabs.addTab(self.sensor_calibration_panel, "Calibration capteur")
        self._tabs.addTab(self.source_geometry_panel, "Géométrie source")
        self._tabs.addTab(self.mechanical_transmission_panel, "Transmission")

        conversion_unit = QTabWidget()
        conversion_unit.setUsesScrollButtons(True)
        conversion_unit.addTab(self.acquisition_throughput_widget, "Microcontrôleur : débit d'acquisition")
        conversion_unit.addTab(self.adc_output_rate_widget, "ADC : cadence de sortie")
        self._tabs.addTab(conversion_unit, _CONVERSION_UNIT_LABEL)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._tabs)
