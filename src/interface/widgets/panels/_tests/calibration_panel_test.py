"""CalibrationPanel: calibrations and characterization measurements only, apart from the component catalog."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from interface.widgets.panels.calibration_panel import CalibrationPanel

UNIT_LABEL = "Unité de conversion entre signaux numériques et analogiques"

_ALIVE = []  # keep top-level test widgets alive across tests (Qt still lays them out)


def _labels(tabs):
    return [tabs.tabText(i) for i in range(tabs.count())]


def _panel():
    QApplication.instance() or QApplication([])
    panel = CalibrationPanel()
    _ALIVE.append(panel)
    return panel


def test_the_calibration_panel_lists_the_calibrations_and_the_unit_measurements():
    panel = _panel()

    top = _labels(panel._tabs)
    assert top == ["Calibration capteur", "Géométrie source", "Transmission", UNIT_LABEL]
    assert panel._tabs.widget(top.index("Transmission")) is panel.mechanical_transmission_panel


def test_the_unit_measurements_are_grouped_under_their_conversion_unit():
    panel = _panel()

    top = _labels(panel._tabs)
    unit = panel._tabs.widget(top.index(UNIT_LABEL))
    assert _labels(unit) == ["Microcontrôleur : débit d'acquisition", "ADC : cadence de sortie"]
    assert unit.isAncestorOf(panel.acquisition_throughput_widget)
    assert unit.isAncestorOf(panel.adc_output_rate_widget)


def test_the_calibration_panel_holds_no_component_catalog():
    panel = _panel()

    assert not hasattr(panel, "add_hardware_component_tab")
    assert not hasattr(panel, "hardware_component_panels")
