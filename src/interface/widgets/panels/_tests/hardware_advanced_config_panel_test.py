import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from domain.shared_kernel.value_objects.hardware_configuration.hardware_advanced_parameter_schema import (
    NumberParameterSchema,
)
from interface.widgets.panels.hardware_advanced_config_panel import HardwareAdvancedConfigPanel


def _spec(key, default, max_value):
    return NumberParameterSchema(
        key=key, display_name=key, description="", default_value=default,
        min_value=0.0, max_value=max_value, group="DDS",
    )


def _make_panel() -> HardwareAdvancedConfigPanel:
    QApplication.instance() or QApplication([])
    panel = HardwareAdvancedConfigPanel()
    panel.set_parameter_specs("ad9106_dds", [
        _spec("ch2_gain", 1100.0, 16376.0),
        _spec("ch2_phase", 32768.0, 65535.0),
        _spec("ch2_offset", 7.0, 65535.0),
        _spec("ch3_gain", 7777.0, 16376.0),
    ])
    return panel


def test_physical_units_display_converts_but_emits_raw_registers():
    panel = _make_panel()
    panel._physical_units_checkbox.setChecked(True)

    # ch1/ch2: 100 % = 5500 (Excitation panel scale); ch3/ch4: 100 % = 10000
    assert abs(panel._widgets["ch2_gain"].value() - 20.0) < 1e-9
    assert abs(panel._widgets["ch3_gain"].value() - 77.77) < 1e-9
    assert abs(panel._widgets["ch2_phase"].value() - 180.0) < 1e-9
    assert panel._widgets["ch2_offset"].value() == 7.0  # not a gain/phase: untouched

    # Lossless round trip to raw registers
    config = panel._get_current_config()
    assert config["ch2_gain"] == 1100
    assert config["ch3_gain"] == 7777
    assert config["ch2_phase"] == 32768

    # Editing in physical units still emits raw register values
    panel._widgets["ch2_gain"].setValue(50.0)
    panel._widgets["ch2_phase"].setValue(90.0)
    config = panel._get_current_config()
    assert config["ch2_gain"] == 2750
    assert config["ch2_phase"] == 16384

    # Gain is capped at 100 % in this mode
    panel._widgets["ch2_gain"].setValue(150.0)
    panel._widgets["ch3_gain"].setValue(150.0)
    config = panel._get_current_config()
    assert config["ch2_gain"] == 5500
    assert config["ch3_gain"] == 10000

    # Toggling back shows the raw registers of what was just edited
    panel._physical_units_checkbox.setChecked(False)
    assert panel._widgets["ch2_gain"].value() == 5500
    assert panel._widgets["ch2_phase"].value() == 16384


def test_arrow_step_applies_immediately_but_typing_waits_for_enter():
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    panel = _make_panel()
    panel._physical_units_checkbox.setChecked(True)
    applied = []
    panel.apply_requested.connect(applied.append)
    phase = panel._widgets["ch2_phase"]

    phase.stepUp()  # same path as clicking the up arrow
    assert len(applied) == 1
    assert applied[0]["ch2_phase"] == round(181.0 * 65536 / 360)

    phase.selectAll()
    QTest.keyClicks(phase, "90")
    assert len(applied) == 1  # nothing written while typing
    QTest.keyClick(phase, Qt.Key.Key_Return)
    assert len(applied) == 2
    assert applied[1]["ch2_phase"] == 16384
