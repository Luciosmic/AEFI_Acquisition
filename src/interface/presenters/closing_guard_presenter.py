"""Turns a refused close into the message the operator reads."""

from PySide6.QtCore import QObject, Signal

from application.closing_guard_service.dtos.close_decision_dto import CloseDecisionDTO, OpenAcquisitionDTO

TITLE = "Acquisition en cours"
# Acquisition kinds as the operator calls them; an unknown kind shows as is.
KIND_LABELS = {
    "step_scan": "scan 2D",
    "fly_scan": "scan au vol",
    "time_series": "lecture continue",
    "frequency_sweep": "balayage en fréquence",
    "acquisition_throughput": "caractérisation du débit d'acquisition",
}


class ClosingGuardPresenter(QObject):
    close_refused = Signal(str, str)  # title, text

    def present_close_refused(self, decision: CloseDecisionDTO) -> None:
        acquisitions = " ; ".join(_describe(a) for a in decision.open_acquisitions)
        self.close_refused.emit(TITLE, (
            f"Une acquisition avec export est en cours ({acquisitions}). "
            "Arrêtez d'abord toute acquisition avant de fermer l'application."
        ))


def _describe(acquisition: OpenAcquisitionDTO) -> str:
    kind = KIND_LABELS.get(acquisition.acquisition_kind, acquisition.acquisition_kind)
    return f"{kind}, objet {acquisition.measured_object}" if acquisition.measured_object else kind
