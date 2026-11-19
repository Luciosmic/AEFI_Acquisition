"""
AcquisitionParametersPresenter - What the "Paramètres d'acquisition" panel shows (see acquisition_parameters_presenter_intention.md).
"""

import logging
from typing import List, Tuple

from ...application.acquisition_catalog_service.dtos.acquisition_status_dto import AcquisitionStatusDTO

logger = logging.getLogger(__name__)

NOT_SAID = "non renseigné"
NO_SELECTION = "Aucune acquisition sélectionnée"
_FROM_ACQUISITION = "ceux de l'acquisition"
_IDEAL = "angles idéaux du gabarit"
_IDEAL_FALLBACK = "angles idéaux du gabarit (repli)"


class AcquisitionParametersPresenter:
    """`view` takes `set_title(text)` and `set_rows([(label, value), ...])`: it shows them as they come."""

    def __init__(self, view):
        self._view = view

    def clear(self) -> None:
        self._view.set_title(NO_SELECTION)
        self._view.set_rows([])

    def show(self, status: AcquisitionStatusDTO) -> None:
        """Show what the parameters file of the acquisition says. Reads nothing, writes no file."""
        rows: List[Tuple[str, str]] = [
            ("Objet mesuré", status.measured_object or NOT_SAID),
            ("Version du schéma", status.schema_version or NOT_SAID),
        ]
        rotation = status.applied_rotation
        if rotation is not None:
            for axis, degrees in zip("xyz", rotation.angles):
                rows.append((f"Angle θ{axis} appliqué", f"{degrees:g} °"))
            rows.append((
                "Convention de rotation",
                f"{rotation.convention_type} · {rotation.convention_order} · {rotation.convention_direction}",
            ))
            if rotation.origin:
                rows.append(("Origine des angles", rotation.origin))
            if rotation.calibration_id:
                rows.append(("Calibration appliquée", rotation.calibration_id))
            used = _FROM_ACQUISITION
        elif status.rotation_problem is not None:
            rows.append(("Rotation inutilisable", status.rotation_problem))
            used = _IDEAL_FALLBACK
        else:
            rows.append(("Angles appliqués", "non renseignés"))
            used = _IDEAL
        rows.append(("Angles utilisés au traitement", used))
        self._view.set_title(status.name)
        self._view.set_rows(rows)
        logger.debug("acquisition_parameters.shown scan=%s rotation=%s", status.name, "applied" if rotation else "none")
