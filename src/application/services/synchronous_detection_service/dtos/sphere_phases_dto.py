from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SpherePhasesDTO:
    """
    Seul objet traversant du `SynchronousDetectionService` vers la couche
    interface pour cette fonctionnalité — les presenters ne doivent jamais
    importer de types `domain/` pour l'afficher.
    """

    s1_degrees: float
    s2_degrees: float
    s3_degrees: float
    s4_degrees: float
    delta_phi_corrige_degrees: Optional[float]
    quadrature_enforced: bool
    lock_in_gain_below_default: bool
