import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from interface.widgets.panels.adc_output_rate_characterization_widget import AdcOutputRateCharacterizationWidget
from interface.widgets.panels.calibration_panel import CalibrationPanel

_ALIVE = []  # keep top-level test widgets alive across tests (Qt still lays them out)


def _keep(widget):
    _ALIVE.append(widget)
    return widget


def _point(osr):
    return SimpleNamespace(oversampling_ratio=osr, output_rate_hz=4.096e6 / osr, interval_std_s=2e-7,
                           regular_interval_count=49, irregular_interval_count=0, implied_modulator_frequency_hz=4.096e6)


def test_buttons_emit_current_osr_or_the_entered_sweep():
    QApplication.instance() or QApplication([])
    widget = _keep(AdcOutputRateCharacterizationWidget())
    widget.set_request_defaults((4096, 2048, 32))
    requests = []
    widget.start_requested.connect(lambda osr, ch, probe, periods: requests.append((osr, ch, probe, periods)))

    widget.btn_current.click()
    widget.btn_sweep.click()

    assert requests == [((), 1, 10.0, 50), ((4096, 2048, 32), 1, 10.0, 50)]


def test_points_and_result_are_shown():
    QApplication.instance() or QApplication([])
    widget = _keep(AdcOutputRateCharacterizationWidget())
    widget.set_running(True)
    widget.add_point(_point(4096))
    widget.add_point(_point(32))
    widget.show_result(SimpleNamespace(points=(_point(4096), _point(32)), mean_modulator_frequency_hz=4.096e6,
                                       max_modulator_frequency_relative_deviation=1e-6, restored_oversampling_ratio=4096,
                                       instrument="DSO-X 2014A"))
    widget.canvas.draw()
    assert widget.table.rowCount() == 2
    assert widget.table.item(1, 1).text() == "128000.0000"
    assert "OSR remis à 4096" in widget.lbl_result.text()


def test_the_widget_lives_in_the_adc_tab():
    QApplication.instance() or QApplication([])
    calibration = _keep(CalibrationPanel())
    kind = SimpleNamespace(key="adc", label="ADC", quantities=())
    panel = calibration.add_hardware_component_tab(kind)
    calibration.adc_output_rate_widget.canvas.draw()  # empty plot must draw
    assert calibration.adc_output_rate_widget.parent() is panel
