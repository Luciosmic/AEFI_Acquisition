from interface.presentation.taskbar_model import TaskbarPresentationModel


def test_add_panel_stores_group_for_taskbar_visual_grouping():
    model = TaskbarPresentationModel()

    model.add_panel("scan_control", "Scan Configuration", group="Scan")
    model.add_panel("logs", "Logs", group="Système")

    groups = [p.group for p in model.panels]
    assert groups == ["Scan", "Système"]


def test_add_panel_group_defaults_to_none():
    model = TaskbarPresentationModel()

    model.add_panel("settings", "Settings")

    assert model.panels[0].group is None
