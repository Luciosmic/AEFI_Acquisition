from application.closing_guard_service.dtos.close_decision_dto import CloseDecisionDTO, OpenAcquisitionDTO
from application.closing_guard_service.i_api_closing_guard_service import IApiClosingGuardService
from interface.close_request_adapter.close_request_adapter import CloseRequestAdapter
from interface.presenters.closing_guard_presenter import ClosingGuardPresenter

REFUSED = CloseDecisionDTO(False, (OpenAcquisitionDTO("step_scan", "scan-1", "plaque"),))
ALLOWED = CloseDecisionDTO(True)


class _Guard(IApiClosingGuardService):
    def __init__(self, decision: CloseDecisionDTO) -> None:
        self.decision = decision

    def can_close(self) -> CloseDecisionDTO:
        return self.decision


class _SessionManager:
    def __init__(self, interaction_allowed: bool = True) -> None:
        self.interaction_allowed = interaction_allowed
        self.cancelled = False

    def allowsInteraction(self) -> bool:
        return self.interaction_allowed

    def cancel(self) -> None:
        self.cancelled = True


def _adapter(decision):
    presenter = ClosingGuardPresenter()
    shown = []
    presenter.close_refused.connect(lambda title, text: shown.append(text))
    return CloseRequestAdapter(_Guard(decision), presenter), shown


def test_la_fenetre_ne_se_ferme_pas_pendant_un_export_et_le_message_s_affiche() -> None:
    adapter, shown = _adapter(REFUSED)
    assert adapter.on_window_close() is False
    assert len(shown) == 1 and "scan 2D, objet plaque" in shown[0]


def test_la_fenetre_se_ferme_sans_export_et_sans_message() -> None:
    adapter, shown = _adapter(ALLOWED)
    assert adapter.on_window_close() is True
    assert shown == []


def test_la_fin_de_session_est_annulee_pendant_un_export_sans_boite_de_message() -> None:
    adapter, shown = _adapter(REFUSED)
    manager = _SessionManager()
    adapter.on_session_end_request(manager)
    assert manager.cancelled
    assert shown == []


def test_la_fin_de_session_passe_sans_export() -> None:
    adapter, _ = _adapter(ALLOWED)
    manager = _SessionManager()
    adapter.on_session_end_request(manager)
    assert not manager.cancelled
