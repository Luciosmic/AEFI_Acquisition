"""StartupView: a startup failure keeps the splash open with the details."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from interface.ui_system_lifecycle.presenter_system_lifecycle import SystemLifecyclePresenter
from interface.ui_system_lifecycle.view_startup import StartupView

_app = QApplication.instance() or QApplication([])


def test_failure_keeps_window_open_with_traceback_and_close_exits_nonzero(monkeypatch):
    view = StartupView(SystemLifecyclePresenter())
    view.show()

    view.show_failure("Traceback (most recent call last):\nRuntimeError: COM8 absent")

    assert view.isVisible()
    assert "COM8 absent" in view.failure_details.toPlainText()
    exit_codes = []
    monkeypatch.setattr(QApplication, "exit", lambda code=0: exit_codes.append(code))
    view.close_button.click()
    assert exit_codes == [1]
