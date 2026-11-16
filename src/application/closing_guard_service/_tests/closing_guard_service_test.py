import logging
from collections import defaultdict
from typing import Any, Callable

from application.closing_guard_service.closing_guard_service import HOLD_REASON, ClosingGuardService
from application.closing_guard_service.dtos.close_decision_dto import OpenAcquisitionDTO
from domain.shared_kernel.events.acquisition_export_closed.acquisition_export_closed import AcquisitionExportClosed
from domain.shared_kernel.events.acquisition_export_opened.acquisition_export_opened import AcquisitionExportOpened
from domain.shared_kernel.events.i_domain_event_bus.i_domain_event_bus import IDomainEventBus
from infrastructure.null_system_session_guard.fake.fake_null_system_session_guard import FakeNullSystemSessionGuard


class _Bus(IDomainEventBus):
    """Synchronous in-test bus: delivers each published event to its subscribers."""

    def __init__(self) -> None:
        self._handlers = defaultdict(list)

    def subscribe(self, event_type: str, handler: Callable[[Any], None]) -> None:
        self._handlers[event_type].append(handler)

    def publish(self, event_type: str, data: Any) -> None:
        for handler in list(self._handlers[event_type]):
            handler(data)

    def unsubscribe(self, event_type: str, handler: Callable[[Any], None]) -> None:
        self._handlers[event_type].remove(handler)

    def clear_subscribers(self, event_type: str = None) -> None:
        self._handlers.clear()


def _guard():
    bus, session = _Bus(), FakeNullSystemSessionGuard()
    return ClosingGuardService(bus, session), bus, session


def _open(bus, kind="step_scan", acquisition_id="scan-1", measured_object="plaque"):
    bus.publish("acquisitionexportopened", AcquisitionExportOpened(
        acquisition_kind=kind, acquisition_id=acquisition_id, measured_object=measured_object))


def _close(bus, kind="step_scan", acquisition_id="scan-1"):
    bus.publish("acquisitionexportclosed", AcquisitionExportClosed(acquisition_kind=kind, acquisition_id=acquisition_id))


def test_sans_export_ouvert_la_fermeture_est_acceptee() -> None:
    guard, _, session = _guard()
    decision = guard.can_close()
    assert decision.allowed
    assert decision.open_acquisitions == ()
    assert session.holds == []


def test_un_export_ouvert_refuse_la_fermeture_et_nomme_l_acquisition() -> None:
    guard, bus, _ = _guard()
    _open(bus)
    decision = guard.can_close()
    assert not decision.allowed
    assert decision.open_acquisitions == (OpenAcquisitionDTO("step_scan", "scan-1", "plaque"),)


def test_l_export_ferme_rend_la_fermeture_possible() -> None:
    guard, bus, _ = _guard()
    _open(bus)
    _close(bus)
    assert guard.can_close().allowed


def test_le_premier_export_ouvert_retient_le_systeme_et_le_dernier_ferme_le_relache() -> None:
    guard, bus, session = _guard()
    _open(bus, "step_scan", "scan-1")
    _open(bus, "frequency_sweep", "sweep-1", "")
    assert session.holds == [HOLD_REASON]
    _close(bus, "step_scan", "scan-1")
    assert session.is_holding
    assert guard.can_close().open_acquisitions == (OpenAcquisitionDTO("frequency_sweep", "sweep-1", ""),)
    _close(bus, "frequency_sweep", "sweep-1")
    assert not session.is_holding
    assert session.releases == 1


def test_une_ouverture_deja_suivie_ne_retient_pas_deux_fois() -> None:
    guard, bus, session = _guard()
    _open(bus)
    _open(bus)
    assert session.holds == [HOLD_REASON]
    _close(bus)
    assert guard.can_close().allowed
    assert session.releases == 1


def test_une_fermeture_inconnue_ne_relache_rien() -> None:
    guard, bus, session = _guard()
    _open(bus, "step_scan", "scan-1")
    _close(bus, "step_scan", "autre")
    assert session.is_holding
    assert not guard.can_close().allowed


def test_la_decision_est_loguee_avec_l_acquisition(caplog) -> None:
    guard, bus, _ = _guard()
    _open(bus)
    with caplog.at_level(logging.INFO):
        guard.can_close()
    assert "refused" in caplog.text and "scan-1" in caplog.text
    _close(bus)
    caplog.clear()
    with caplog.at_level(logging.INFO):
        guard.can_close()
    assert "accepted" in caplog.text
