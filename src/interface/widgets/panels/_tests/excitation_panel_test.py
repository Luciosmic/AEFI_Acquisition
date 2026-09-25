import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from interface.widgets.panels.excitation_panel import phase_to_sphere_color


def _c(phase):
    return phase_to_sphere_color(phase).name()


def test_sphere_color_follows_applied_phase_not_selected_mode():
    red, blue = _c(0.0), _c(180.0)
    assert red != blue
    assert _c(359.9) == red  # wraps around 0°
    assert _c(90.0) != _c(270.0)
    # Non-canonical phase (failed write / manual edit) must stand out
    anomalous = _c(45.0)
    assert anomalous not in {red, blue, _c(90.0), _c(270.0)}
    # No hardware reading yet -> neutral, distinct from everything above
    assert _c(None) not in {red, blue, anomalous}
