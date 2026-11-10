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


def test_increments_are_shown_raw_whatever_the_referential():
    panel = _make_panel()
    panel.set_axis_limits(1270.0, 1270.0)
    panel.set_referential_mode("centered")

    panel.update_increments(12345, -678)

    assert panel.lbl_increments.text() == "Incréments  X: 12345   Y: -678"


def test_increment_setpoints_are_emitted_in_increments_and_work_when_not_calibrated():
    from types import SimpleNamespace

    panel = _make_panel()
    panel.set_calibration_banner(SimpleNamespace(visible=True, text="non calibré"))
    assert not panel.btn_go_x.isEnabled()  # mm moves are blocked without conversion

    panel.update_increments(6290, 100)
    panel.combo_unit.setCurrentText("incréments")

    assert panel.btn_go_x.isEnabled() and panel.btn_go_both.isEnabled()
    assert (panel.spin_to_x.value(), panel.spin_to_y.value()) == (6290, 100)  # starts at the current position
    sent = []
    panel.move_to_increments_requested.connect(lambda x, y: sent.append((x, y)))
    panel.spin_to_x.setValue(2000)
    panel.spin_to_y.setValue(300)

    panel.btn_go_x.click()
    panel.btn_go_y.click()
    panel.btn_go_both.click()

    assert sent == [(2000, None), (None, 300), (2000, 300)]

    panel.combo_unit.setCurrentText("mm")
    assert not panel.btn_go_x.isEnabled()  # back to mm: blocked again while not calibrated
