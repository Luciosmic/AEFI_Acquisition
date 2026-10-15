import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from interface.view_models.aefi_spectral_analysis_view_model import AefiSpectralAnalysisViewModel
from interface.widgets.panels.aefi_spectral_analysis_panel import AefiSpectralAnalysisPanel

_ALIVE = []  # keep top-level test widgets alive across tests (Qt still lays them out)


def _panel():
    QApplication.instance() or QApplication([])
    panel = AefiSpectralAnalysisPanel()
    _ALIVE.append(panel)
    return panel


def test_window_duration_change_emits_signal():
    panel = _panel()
    emitted = []
    panel.window_duration_changed.connect(emitted.append)

    panel.spin_window_duration.setValue(5.0)

    assert emitted == [5.0]


def test_on_spectrum_updated_plots_channel_curves_and_sample_count():
    panel = _panel()
    vm = AefiSpectralAnalysisViewModel(
        frequencies_hz=[0.0, 1.0, 2.0],
        amplitudes_by_channel={
            "Ux In-Phase": [0.1, 0.2, 0.3],
            "Ux Quadrature": [0.0, 0.0, 0.0],
            "Uy In-Phase": [0.0, 0.0, 0.0],
            "Uy Quadrature": [0.0, 0.0, 0.0],
            "Uz In-Phase": [0.0, 0.0, 0.0],
            "Uz Quadrature": [0.0, 0.0, 0.0],
        },
        window_start_iso="2026-10-09T00:00:00+00:00",
        window_end_iso="2026-10-09T00:00:02+00:00",
        sample_count=300,
    )

    panel.on_spectrum_updated(vm)

    x_data, y_data = panel.curves["Ux In-Phase"].getData()
    assert list(x_data) == [0.0, 1.0, 2.0]
    assert list(y_data) == [0.1, 0.2, 0.3]
    assert panel.lbl_sample_count.text() == "300"


def test_channel_toggle_hides_curve():
    panel = _panel()
    btn = panel.channel_checkboxes["Ux In-Phase"]
    assert btn.isChecked()
    assert panel.curves["Ux In-Phase"].isVisible()

    btn.setChecked(False)
    panel._on_channel_toggled()

    assert not panel.curves["Ux In-Phase"].isVisible()
