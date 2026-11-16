"""The operator's path, as main.py composes it: the real main window wired by the real wiring function,
the guard, its adapter and presenter created in a scope that returns, garbage collected, then the window
is closed the way the cross, Alt+F4 or the taskbar close it (a QCloseEvent)."""

import gc

from PySide6.QtCore import SIGNAL
from PySide6.QtWidgets import QApplication

from application.closing_guard_service.closing_guard_service import ClosingGuardService
from domain.shared_kernel.events.acquisition_export_closed.acquisition_export_closed import AcquisitionExportClosed
from domain.shared_kernel.events.acquisition_export_opened.acquisition_export_opened import AcquisitionExportOpened
from infrastructure.in_memory_event_bus.in_memory_event_bus import InMemoryEventBus
from infrastructure.null_system_session_guard.fake.fake_null_system_session_guard import FakeNullSystemSessionGuard
from interface.close_request_adapter.close_request_adapter import CloseRequestAdapter
from interface.presenters.closing_guard_presenter import ClosingGuardPresenter
from interface.shell import dashboard as dashboard_module
from interface.shell.dashboard import Dashboard
from interface.shell.dashboard_wiring import wire_closing_guard


def _compose(app, dashboard, event_bus, session_guard) -> None:
    """Like main.py: service, presenter and adapter are locals of a function that returns."""
    service = ClosingGuardService(event_bus, session_guard)
    presenter = ClosingGuardPresenter()
    wire_closing_guard(app, dashboard, CloseRequestAdapter(service, presenter), presenter)


def _composed(monkeypatch, tmp_path):
    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(Dashboard, "LAYOUT_FILE", str(tmp_path / "layout.dat"))
    shown = []
    monkeypatch.setattr(dashboard_module.QMessageBox, "warning", lambda parent, title, text: shown.append((title, text)))
    event_bus, session_guard, dashboard = InMemoryEventBus(), FakeNullSystemSessionGuard(), Dashboard()
    _compose(app, dashboard, event_bus, session_guard)
    gc.collect()
    dashboard.show()
    return app, dashboard, event_bus, session_guard, shown


def test_pendant_un_export_la_croix_laisse_la_fenetre_ouverte_et_affiche_le_message(monkeypatch, tmp_path):
    _, dashboard, event_bus, session_guard, shown = _composed(monkeypatch, tmp_path)
    event_bus.publish("acquisitionexportopened", AcquisitionExportOpened(
        acquisition_kind="step_scan", acquisition_id="scan-1", measured_object="plaque"))

    assert dashboard.close() is False
    assert dashboard.isVisible()
    assert [title for title, _ in shown] == ["Acquisition en cours"]
    assert "scan 2D, objet plaque" in shown[0][1]
    assert session_guard.is_holding
    assert not (tmp_path / "layout.dat").exists()  # nothing saved for a close that did not happen


def test_une_fois_l_export_ferme_la_croix_ferme_la_fenetre_et_garde_la_disposition(monkeypatch, tmp_path):
    _, dashboard, event_bus, session_guard, shown = _composed(monkeypatch, tmp_path)
    event_bus.publish("acquisitionexportopened", AcquisitionExportOpened(acquisition_kind="step_scan", acquisition_id="scan-1"))
    event_bus.publish("acquisitionexportclosed", AcquisitionExportClosed(acquisition_kind="step_scan", acquisition_id="scan-1"))

    assert dashboard.close() is True
    assert not dashboard.isVisible()
    assert shown == []
    assert not session_guard.is_holding
    assert (tmp_path / "layout.dat").exists()


def test_la_demande_de_fin_de_session_est_reliee_a_la_garde(monkeypatch, tmp_path):
    app, *_ = _composed(monkeypatch, tmp_path)
    assert app.receivers(SIGNAL("commitDataRequest(QSessionManager&)")) >= 1
