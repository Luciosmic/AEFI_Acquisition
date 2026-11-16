from application.closing_guard_service.dtos.close_decision_dto import CloseDecisionDTO, OpenAcquisitionDTO
from interface.presenters.closing_guard_presenter import ClosingGuardPresenter


def _shown(decision):
    presenter = ClosingGuardPresenter()
    shown = []
    presenter.close_refused.connect(lambda title, text: shown.append((title, text)))
    presenter.present_close_refused(decision)
    return shown


def test_le_message_nomme_le_scan_et_son_objet_et_dit_d_arreter_d_abord() -> None:
    ((title, text),) = _shown(CloseDecisionDTO(False, (OpenAcquisitionDTO("step_scan", "scan-1", "plaque"),)))
    assert title == "Acquisition en cours"
    assert text == (
        "Une acquisition avec export est en cours (scan 2D, objet plaque). "
        "Arrêtez d'abord toute acquisition avant de fermer l'application."
    )


def test_sans_objet_mesure_le_message_ne_nomme_que_la_sorte() -> None:
    ((_, text),) = _shown(CloseDecisionDTO(False, (OpenAcquisitionDTO("frequency_sweep", "sweep-1", ""),)))
    assert "(balayage en fréquence)" in text


def test_plusieurs_acquisitions_sont_toutes_nommees() -> None:
    ((_, text),) = _shown(CloseDecisionDTO(False, (
        OpenAcquisitionDTO("time_series", "a-1", "plaque"),
        OpenAcquisitionDTO("acquisition_throughput", "t-1", ""),
    )))
    assert "(lecture continue, objet plaque ; caractérisation du débit d'acquisition)" in text


def test_une_sorte_inconnue_s_affiche_telle_quelle() -> None:
    ((_, text),) = _shown(CloseDecisionDTO(False, (OpenAcquisitionDTO("nouvelle_sorte", "x-1", ""),)))
    assert "(nouvelle_sorte)" in text
