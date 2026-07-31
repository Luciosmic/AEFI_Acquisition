import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from interface.widgets.scope.scope_window_control import ScopeWindowControl


def _make_control() -> ScopeWindowControl:
    QApplication.instance() or QApplication([])
    return ScopeWindowControl(default_window_s=5.0)


def test_from_start_mode_returns_full_buffer_untouched():
    ctl = _make_control()
    ctl.mode_combo.setCurrentText("From start")
    times = [0.0, 1.0, 2.0, 10.0]
    values = {"X": [0, 1, 2, 3]}

    t_plot, values_plot = ctl.visible_slice(times, values)

    assert t_plot is times
    assert values_plot is values


def test_sliding_mode_keeps_only_last_window_seconds():
    ctl = _make_control()
    ctl.mode_combo.setCurrentText("Sliding window")
    ctl.duration_spin.setValue(5.0)
    times = [0.0, 1.0, 4.0, 6.0, 9.9, 10.0]
    values = {"X": [0, 1, 2, 3, 4, 5]}

    t_plot, values_plot = ctl.visible_slice(times, values)

    assert t_plot == [6.0, 9.9, 10.0]
    assert values_plot["X"] == [3, 4, 5]


def test_sliding_mode_before_buffer_exceeds_window_shows_everything():
    ctl = _make_control()
    ctl.mode_combo.setCurrentText("Sliding window")
    ctl.duration_spin.setValue(50.0)
    times = [0.0, 1.0, 2.0]
    values = {"X": [0, 1, 2]}

    t_plot, values_plot = ctl.visible_slice(times, values)

    assert t_plot == times
    assert values_plot["X"] == [0, 1, 2]
