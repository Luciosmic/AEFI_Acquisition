import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from application.operator_registry.operator_service.dtos.operator_dto import OperatorDTO
from application.services.measured_object_service.dtos.measured_object_dto import MeasuredObjectDTO

from interface.widgets.panels.scan_control_panel import ScanControlPanel

_ALIVE = []  # keep top-level test widgets alive across tests (Qt still lays them out)


def test_start_carries_the_measured_object_and_the_operator():
    QApplication.instance() or QApplication([])
    panel = ScanControlPanel()
    _ALIVE.append(panel)
    emitted = []
    panel.scan_start_requested.connect(emitted.append)
    panel.measured_object_selector.set_measured_objects([MeasuredObjectDTO(measured_object_id="id-plaque", name="plaque de cuivre 20 mm")])
    panel.measured_object_selector.activated.emit(panel.measured_object_selector.findText("plaque de cuivre 20 mm"))
    panel.operator_selector.set_operators([OperatorDTO(operator_id="id-luis", name="Luis")])
    index = panel.operator_selector.findText("Luis")
    panel.operator_selector.setCurrentIndex(index)
    panel.operator_selector.activated.emit(index)

    panel._on_start_clicked()

    assert (emitted[0]["measured_object_id"], emitted[0]["measured_object"]) == ("id-plaque", "plaque de cuivre 20 mm")
    assert (emitted[0]["operator_id"], emitted[0]["operator"]) == ("id-luis", "Luis")


class _Store:
    """In-memory UIConfigStore: no runtime config file is read or written."""

    def __init__(self, referential_mode="limit_switch", scan_config=None):
        self.referential_mode = referential_mode
        self.scan_config = scan_config or {}
        self.saved_scan_config = None

    def load_motion_config(self):
        return {"referential_mode": self.referential_mode}

    def load_scan_config(self):
        return self.scan_config

    def load_export_config(self):
        return {}

    def save_scan_config(self, scan_config):
        self.saved_scan_config = scan_config


def _panel(store=None, limits=(1200.0, 1160.0)):
    QApplication.instance() or QApplication([])
    panel = ScanControlPanel(config_store=store or _Store())
    _ALIVE.append(panel)
    panel.set_axis_limits(*limits)
    emitted = []
    panel.scan_start_requested.connect(emitted.append)
    return panel, emitted


def _zone(panel):
    return tuple(
        float(field.text())
        for field in (panel.input_x_min, panel.input_x_max, panel.input_y_min, panel.input_y_max)
    )


def test_limit_switch_referential_sends_the_zone_as_typed():
    panel, emitted = _panel()
    panel.input_x_min.setText("610.5")

    panel._on_start_clicked()

    assert (emitted[0]["x_min"], emitted[0]["x_max"]) == ("610.5", "800.0")
    assert "butées" in panel.lbl_referential.text()


def test_switching_to_centered_rewrites_the_same_physical_zone_around_the_middle():
    panel, emitted = _panel()  # travel 1200 x 1160 mm: the middle is (600, 580)

    panel.set_referential_mode("centered")

    assert _zone(panel) == (0.0, 200.0, 20.0, 220.0)
    assert "centré" in panel.lbl_referential.text()
    panel._on_start_clicked()
    assert [emitted[0][k] for k in ("x_min", "x_max", "y_min", "y_max")] == ["600.0", "800.0", "600.0", "800.0"]


def test_values_typed_in_the_centered_referential_are_sent_from_the_limit_switches():
    panel, emitted = _panel()
    panel.set_referential_mode("centered")

    panel.input_x_min.setText("-100")
    panel.input_y_max.setText("50")
    panel.input_line_center_x.setText("0")
    panel.input_line_center_y.setText("-10")
    panel._on_start_clicked()

    assert emitted[0]["x_min"] == "500.0"
    assert emitted[0]["y_max"] == "630.0"
    assert (emitted[0]["line_center_x"], emitted[0]["line_center_y"]) == ("600.0", "570.0")


def test_switching_back_restores_the_limit_switch_values():
    panel, _ = _panel()

    panel.set_referential_mode("centered")
    panel.set_referential_mode("limit_switch")

    assert _zone(panel) == (600.0, 800.0, 600.0, 800.0)


def test_a_new_travel_moves_the_middle_not_the_physical_zone():
    """The factor µm/increment was corrected: the centre moves in mm, the zone must stay where it is."""
    panel, emitted = _panel()
    panel.set_referential_mode("centered")

    panel.set_axis_limits(1250.0, 1160.0)

    assert _zone(panel)[:2] == (-25.0, 175.0)
    panel._on_start_clicked()
    assert (emitted[0]["x_min"], emitted[0]["x_max"]) == ("600.0", "800.0")


def test_defaults_are_saved_in_the_limit_switch_referential_whatever_the_display():
    store = _Store()
    panel, _ = _panel(store)
    panel.set_referential_mode("centered")

    panel._save_scan_defaults()

    assert (store.saved_scan_config["x_min"], store.saved_scan_config["y_max"]) == (600.0, 800.0)


def test_it_starts_in_the_referential_saved_by_the_settings_panel():
    store = _Store("centered", {"x_min": 650.0, "x_max": 750.0, "y_min": 580.0, "y_max": 680.0})
    panel, _ = _panel(store)

    assert _zone(panel) == (50.0, 150.0, 0.0, 100.0)


def _shown(widget):
    return not widget.isHidden()


def test_fly_scan_hides_the_step_scan_only_settings_and_keeps_the_common_ones():
    panel, _ = _panel(_Store(scan_config={"differential_expanded": True}))
    step_only = (panel.input_averaging, panel.btn_toggle_differential, panel.differential_box)
    assert all(_shown(w) for w in step_only)

    panel.radio_fly.setChecked(True)

    assert not any(_shown(w) for w in step_only)
    assert all(_shown(w) for w in (panel.combo_pattern, panel.combo_axis, panel.input_stabilization))
    assert "début de chaque ligne" in panel.input_stabilization.toolTip()


def test_differential_left_checked_is_not_sent_with_a_fly_scan():
    panel, emitted = _panel()
    panel.checkbox_differential_mode.setChecked(True)
    panel.radio_fly.setChecked(True)

    panel._on_start_clicked()

    assert (emitted[0]["fly_scan"], emitted[0]["differential_mode"]) == (True, False)


def test_differential_fold_state_is_saved_with_the_defaults():
    store = _Store()
    panel, _ = _panel(store)
    panel.btn_toggle_differential.setChecked(True)

    panel._save_scan_defaults()

    assert store.saved_scan_config["differential_expanded"] is True


def test_start_carries_the_lift_off_in_mm_or_none_when_empty():
    panel, emitted = _panel()
    panel._on_start_clicked()
    panel.input_lift_off.setText("8,5")
    panel._on_start_clicked()

    assert [e["lift_off_mm"] for e in emitted] == [None, 8.5]
