import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from interface.widgets.panels.external_modules_panel import ExternalModulesPanel


def _make_panel() -> ExternalModulesPanel:
    QApplication.instance() or QApplication([])
    return ExternalModulesPanel()


def test_launch_dispatches_to_the_matching_launcher_entry():
    panel = _make_panel()
    calls = []
    panel._launch = lambda key, script_parts, label: calls.append((key, script_parts, label))

    panel.launch("cube")

    assert calls == [
        ("cube", ("external_modules", "cube_visualizer", "main.py"), "Visualiseur 3D (cube senseur)")
    ]


def test_launch_with_unknown_key_does_nothing():
    panel = _make_panel()
    panel._launch = lambda *a: (_ for _ in ()).throw(AssertionError("should not be called"))

    panel.launch("does-not-exist")
