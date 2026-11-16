"""StartupView: only the loading bar at first; the logs (with their Debug / Warning boxes) appear once
a line is actually written; the application's own icon shows in the window."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from interface.ui_system_lifecycle.presenter_system_lifecycle import SystemLifecyclePresenter
from interface.ui_system_lifecycle.view_startup import StartupView
from interface.widgets.panels.logs_panel import LogsPanel

_app = QApplication.instance() or QApplication([])
APP_ICON = QIcon(str(Path(__file__).resolve().parents[1] / "interface" / "assets" / "app_icon.ico"))


def _shown_view():
    logs = LogsPanel()
    view = StartupView(SystemLifecyclePresenter(), logs_panel=logs, icon=APP_ICON)
    view.show()
    _app.processEvents()
    return view, logs


def test_au_chargement_seule_la_barre_est_visible():
    view, logs = _shown_view()
    assert view.progress_bar.isVisible()
    assert not logs.isVisible()
    assert view.height() < 150


def test_la_premiere_ligne_de_log_agrandit_la_fenetre_avec_les_cases_debug_et_warning():
    view, logs = _shown_view()
    compact_height = view.height()

    logs.append_line("INFO interface.main: Hardware config: mock")
    _app.processEvents()

    assert logs.isVisible()
    assert logs.debug_checkbox.isVisible() and logs.warning_checkbox.isVisible()
    assert view.height() > compact_height


def test_une_ligne_vide_n_agrandit_pas_la_fenetre():
    view, logs = _shown_view()
    logs.append_line("\n")
    _app.processEvents()
    assert not logs.isVisible()


def test_un_echec_agrandit_la_fenetre_pour_montrer_le_detail():
    view, _ = _shown_view()
    view.show_failure("Traceback: RuntimeError: COM8 absent")
    _app.processEvents()
    assert view.failure_details.isVisible()
    assert view.height() > 150


def test_l_icone_de_l_application_est_dans_la_fenetre():
    view, _ = _shown_view()
    assert view.icon_label.isVisible()
    assert not view.icon_label.pixmap().isNull()
    assert not view.windowIcon().isNull()
