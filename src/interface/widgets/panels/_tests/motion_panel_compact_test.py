import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from interface.widgets.panels.motion_panel_compact import MotionPanelCompact


class _FakeConfigStore:
    """In-memory stand-in for UIConfigStore — avoids touching .aefi_acquisition/configs/ in tests."""

    def __init__(self):
        self._data = {}

    def load_motion_config(self):
        return dict(self._data)

    def save_motion_config(self, config):
        self._data = dict(config)


def _make_panel() -> MotionPanelCompact:
    QApplication.instance() or QApplication([])
    return MotionPanelCompact(config_store=_FakeConfigStore())


def test_centered_referential_shifts_display_and_round_trips_target():
    panel = _make_panel()
    panel.set_axis_limits(1270.0, 1270.0)
    panel.set_referential_mode("centered")

    panel.update_position(635.0, 635.0)  # bench center -> displayed origin
    assert panel.lbl_x.text() == "X: 0.00"
    assert panel.lbl_y.text() == "Y: 0.00"

    panel.update_position(0.0, 1270.0)  # opposite corner
    assert panel.lbl_x.text() == "X: -635.00"
    assert panel.lbl_y.text() == "Y: 635.00"

    # Values typed in the centered referential must round-trip to raw mm before a move is emitted.
    assert panel._display_to_raw_x(-635.0) == 0.0
    assert panel._display_to_raw_y(635.0) == 1270.0

    panel.set_referential_mode("limit_switch")
    panel.update_position(0.0, 1270.0)
    assert panel.lbl_x.text() == "X: 0.00"
    assert panel.lbl_y.text() == "Y: 1270.00"
