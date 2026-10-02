import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from interface.widgets.panels.acquisition_throughput_characterization_widget import (
    AcquisitionThroughputCharacterizationWidget,
)
from interface.widgets.panels.calibration_panel import CalibrationPanel

# Top-level test widgets are kept alive: a widget collected by Python while Qt
# still lays it out (next test) makes the matplotlib canvas' sizeHint fail.
_ALIVE = []


def _keep(widget):
    _ALIVE.append(widget)
    return widget


def _point(n_avg):
    return SimpleNamespace(
        n_avg=n_avg, sample_period_s=0.01 + n_avg / 1000, sample_rate_per_s=1 / (0.01 + n_avg / 1000),
        adc_conversions_per_s=n_avg / (0.01 + n_avg / 1000), noise_rms_v=1e-5, noise_in_one_second_v=1e-6,
    )


def _microcontroller_kind():
    return SimpleNamespace(
        key="microcontroller",
        label="Microcontrôleur",
        quantities=(
            SimpleNamespace(key="max_acquisition_rate_per_s", label="Débit max", unit="mesures/s", curve_x_label=None),
            SimpleNamespace(key="optimal_acquisition_rate_per_s", label="Débit optimal", unit="mesures/s",
                            curve_x_label="n_avg"),
        ),
    )


def test_points_fill_the_table_and_running_locks_the_button():
    QApplication.instance() or QApplication([])
    widget = _keep(AcquisitionThroughputCharacterizationWidget())

    widget.set_running(True)
    widget.add_point(_point(1))
    widget.add_point(_point(8))

    assert not widget.btn_start.isEnabled()
    assert widget.table.rowCount() == 2
    assert widget.table.item(1, 0).text() == "8"
    assert widget.table.item(0, 1).text() == "11.00"  # ms


def test_start_emits_the_entered_grid_and_samples():
    QApplication.instance() or QApplication([])
    widget = _keep(AcquisitionThroughputCharacterizationWidget())
    widget.set_request_defaults((1, 2, 4), 50)
    requests = []
    widget.start_requested.connect(lambda values, samples: requests.append((values, samples)))

    widget.edit_n_avg_values.setText("20, 40 60;80")
    widget.spin_samples_per_point.setValue(200)
    widget.btn_start.click()

    assert requests == [((20, 40, 60, 80), 200)]


def test_unreadable_grid_is_refused_in_the_panel():
    QApplication.instance() or QApplication([])
    widget = _keep(AcquisitionThroughputCharacterizationWidget())
    requests = []
    widget.start_requested.connect(lambda values, samples: requests.append(values))

    widget.edit_n_avg_values.setText("20, quarante")
    widget.btn_start.click()

    assert requests == []
    assert widget.lbl_status.text().startswith("Erreur")


def test_result_shows_the_recommendation():
    QApplication.instance() or QApplication([])
    widget = _keep(AcquisitionThroughputCharacterizationWidget())

    widget.show_result(SimpleNamespace(
        points=(_point(1), _point(8)), overhead_s=0.01, adc_output_rate_hz=None, fit_max_relative_residual=0.02,
        recommended_n_avg=8, noise_relative_uncertainty=0.1, oversampling_ratio=4096, excitation="coupée",
    ))

    assert "n_avg recommandé : 8" in widget.lbl_result.text()
    assert "±10 %" in widget.lbl_result.text()
    assert "non résolue" in widget.lbl_result.text()


def test_the_widget_lives_in_the_microcontroller_tab_and_prefills_its_form():
    QApplication.instance() or QApplication([])
    calibration = _keep(CalibrationPanel())
    panel = calibration.add_hardware_component_tab(_microcontroller_kind())

    assert calibration.acquisition_throughput_widget.parent() is panel
    panel.prefill_values({"max_acquisition_rate_per_s": 90.9, "optimal_acquisition_rate_per_s": ((1, 90.9), (8, 55.6))})

    edit, unknown = panel._fields["optimal_acquisition_rate_per_s"]
    assert not unknown.isChecked()
    assert edit.text() == "1:90.9; 8:55.6"
