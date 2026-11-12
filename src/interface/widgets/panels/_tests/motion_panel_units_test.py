"""MotionPanelCompact: one unit (mm / increments) for the whole panel, and the referential chosen in it."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from types import SimpleNamespace

from PySide6.QtWidgets import QApplication

from interface.widgets.panels.motion_panel_compact import MotionPanelCompact


class _FakeConfigStore:
    """In-memory stand-in for UIConfigStore: no runtime config file is touched."""

    def __init__(self):
        self._data = {}

    def load_motion_config(self):
        return dict(self._data)

    def save_motion_config(self, config):
        self._data = dict(config)


def _make_panel() -> MotionPanelCompact:
    QApplication.instance() or QApplication([])
    return MotionPanelCompact(config_store=_FakeConfigStore())


def _banner(visible):
    return SimpleNamespace(visible=visible, text="Banc non calibré" if visible else "")


def test_the_unit_applies_to_the_position_readout_too():
    panel = _make_panel()
    panel.set_axis_limits(1200.0, 1160.0)
    panel.update_position(135.0, 12.5)
    panel.update_increments(6547, 606)

    assert panel.lbl_x.text() == "X: 135.00"
    assert panel.lbl_increments.text() == "Incréments  X: 6547   Y: 606"

    panel.combo_unit.setCurrentText(panel.UNIT_INCREMENTS)

    assert (panel.lbl_x.text(), panel.lbl_y.text()) == ("X: 6547", "Y: 606")
    assert panel.lbl_increments.text() == "mm  X: 135.00   Y: 12.50"


def test_in_increments_the_mm_line_says_unknown_until_the_bench_is_calibrated():
    panel = _make_panel()
    panel.update_increments(10, 20)

    panel.combo_unit.setCurrentText(panel.UNIT_INCREMENTS)

    assert panel.lbl_increments.text() == "mm  X: —   Y: —"


def test_the_jog_step_follows_the_unit_and_is_remembered_per_unit():
    panel = _make_panel()
    jogs_mm, jogs_inc = [], []
    panel.jog_requested.connect(lambda dx, dy: jogs_mm.append((dx, dy)))
    panel.jog_increments_requested.connect(lambda dx, dy: jogs_inc.append((dx, dy)))

    panel.spin_step.setValue(20)
    panel.btn_right.click()
    panel.combo_unit.setCurrentText(panel.UNIT_INCREMENTS)
    assert panel.lbl_step_unit.text() == "inc"
    assert panel.spin_step.value() == 1000  # its own default, not 20 mm read as 20 increments
    panel.spin_step.setValue(250)
    panel.btn_up.click()
    panel.btn_left.click()
    panel.combo_unit.setCurrentText(panel.UNIT_MM)

    assert jogs_mm == [(20.0, 0.0)]
    assert jogs_inc == [(0, 250), (-250, 0)]
    assert panel.spin_step.value() == 20 and panel.lbl_step_unit.text() == "mm"


def test_a_jog_in_increments_works_on_an_uncalibrated_bench_a_jog_in_mm_does_not():
    panel = _make_panel()
    panel.set_calibration_banner(_banner(True))
    assert not panel.btn_right.isEnabled()

    panel.combo_unit.setCurrentText(panel.UNIT_INCREMENTS)
    assert panel.btn_right.isEnabled()

    panel.set_jog_enabled(False)  # axes moving
    assert not panel.btn_right.isEnabled()
    panel.set_jog_enabled(True)
    panel.combo_unit.setCurrentText(panel.UNIT_MM)
    assert not panel.btn_right.isEnabled()


def test_choosing_the_referential_here_shifts_the_display_and_tells_the_others():
    panel = _make_panel()
    panel.set_axis_limits(1200.0, 1160.0)
    panel.update_position(600.0, 580.0)
    chosen = []
    panel.referential_changed.connect(chosen.append)

    panel.combo_referential.setCurrentIndex(1)
    panel.combo_referential.activated.emit(1)  # the operator's pick

    assert chosen == ["centered"]
    assert (panel.lbl_x.text(), panel.lbl_y.text()) == ("X: 0.00", "Y: 0.00")
    assert panel._config_store.load_motion_config()["referential_mode"] == "centered"


def test_the_referential_follows_a_change_from_elsewhere_without_echoing_it():
    panel = _make_panel()
    chosen = []
    panel.referential_changed.connect(chosen.append)

    panel.set_referential_mode("centered")

    assert panel.combo_referential.currentData() == "centered"
    assert chosen == []


def test_the_referential_does_not_apply_to_increments():
    panel = _make_panel()

    panel.combo_unit.setCurrentText(panel.UNIT_INCREMENTS)
    assert not panel.combo_referential.isEnabled()

    panel.combo_unit.setCurrentText(panel.UNIT_MM)
    assert panel.combo_referential.isEnabled()
