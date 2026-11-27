"""BenchConfigurationPanel: the component catalog and its mountings, apart from the calibrations."""
import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from interface.widgets.panels.bench_configuration_panel import BenchConfigurationPanel

UNIT_KEY = "digital_analog_signals_processing_unit"
UNIT_LABEL = "Unité de conversion entre signaux numériques et analogiques"

_ALIVE = []  # keep top-level test widgets alive across tests (Qt still lays them out)


def _keep(widget):
    _ALIVE.append(widget)
    return widget


def _kind(key, label, assembly_key=None, assembly_label=None):
    return SimpleNamespace(key=key, label=label, quantities=(), assembly_key=assembly_key, assembly_label=assembly_label)


def _labels(tabs):
    return [tabs.tabText(i) for i in range(tabs.count())]


def _panel_with_every_kind():
    QApplication.instance() or QApplication([])
    panel = _keep(BenchConfigurationPanel())
    for kind in (
        _kind("sensor", "Capteur"),
        _kind("conditioning_electronics_board", "Carte de conditionnement"),
        _kind("excitation_electronics_board", "Amplification de l'excitation"),
        _kind("signal_generation_chip", "DDS", UNIT_KEY, UNIT_LABEL),
        _kind("adc", "ADC", UNIT_KEY, UNIT_LABEL),
        _kind("microcontroller", "Microcontrôleur", UNIT_KEY, UNIT_LABEL),
        _kind("motors", "Moteurs"),
        _kind("stepper_driver", "Driver pas à pas"),
    ):
        panel.add_hardware_component_tab(kind)
    return panel


def test_components_are_grouped_under_electronique_and_mouvement():
    panel = _panel_with_every_kind()

    top = _labels(panel._tabs)
    assert top == ["Capteur", "Électronique", "Mouvement"]
    electronics = panel._tabs.widget(top.index("Électronique"))
    motion = panel._tabs.widget(top.index("Mouvement"))
    assert _labels(electronics) == ["Carte de conditionnement", "Amplification de l'excitation", UNIT_LABEL]
    assert _labels(motion) == ["Moteurs", "Driver pas à pas"]


def test_dds_adc_and_microcontroller_are_grouped_under_their_conversion_unit():
    panel = _panel_with_every_kind()

    electronics = panel._tabs.widget(_labels(panel._tabs).index("Électronique"))
    unit = electronics.widget(_labels(electronics).index(UNIT_LABEL))
    assert _labels(unit) == ["DDS", "ADC", "Microcontrôleur"]
    assert unit.widget(1) is panel.hardware_component_panels["adc"]


def test_the_configuration_panel_holds_no_calibration():
    panel = _panel_with_every_kind()

    assert not hasattr(panel, "mechanical_transmission_panel")
    assert not hasattr(panel, "sensor_calibration_panel")
    assert not hasattr(panel, "acquisition_throughput_widget")
