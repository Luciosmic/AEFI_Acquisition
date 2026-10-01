import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from interface.presentation.taskbar_model import TaskbarPresentationModel
from interface.widgets.taskbar.modern_taskbar import ModernTaskbar


def _make_taskbar() -> ModernTaskbar:
    QApplication.instance() or QApplication([])
    return ModernTaskbar()


def test_grouped_panels_share_one_button_with_a_menu_action_each():
    taskbar = _make_taskbar()
    model = TaskbarPresentationModel()
    model.add_panel("scan_control", "Scan Configuration", group="Scan")
    model.add_panel("aefi_voltage_map", "AEFI Voltage Map", group="Scan")
    model.add_panel("logs", "Logs", group="Système")

    taskbar.render(model)

    assert list(taskbar.group_buttons.keys()) == ["Scan", "Système"]
    assert set(taskbar.panel_actions.keys()) == {"scan_control", "aefi_voltage_map", "logs"}
    assert len(taskbar.group_menus["Scan"].actions()) == 2


def test_menu_action_checked_state_follows_panel_visibility():
    taskbar = _make_taskbar()
    model = TaskbarPresentationModel()
    model.add_panel("scan_control", "Scan Configuration", group="Scan")
    taskbar.render(model)

    assert taskbar.panel_actions["scan_control"].isChecked() is True

    model.set_panel_visibility("scan_control", False)
    taskbar.render(model)

    assert taskbar.panel_actions["scan_control"].isChecked() is False
    assert taskbar.group_buttons["Scan"].property("active") is False


def test_add_action_group_builds_a_button_that_triggers_callback_with_key():
    taskbar = _make_taskbar()
    triggered = []

    taskbar.add_action_group("External Modules", [("post", "Post"), ("cube", "Cube")], triggered.append)

    button = taskbar.layout_container.itemAt(0).widget()
    assert button.text() == "External Modules  ▾"
    menu = button.menu()
    assert [a.text() for a in menu.actions()] == ["Post", "Cube"]

    menu.actions()[1].trigger()
    assert triggered == ["cube"]
