"""
AefiPoint Repository Port

Responsibility:
- Contrat de persistance des agrégats AefiPoint.

Rationale:
- Le handler de Scan compte les points acquis d'un scan dans une transaction séparée ;
  sans port, il lirait l'état des points via le service applicatif.

Design:
- Le domaine déclare QUOI persister ; l'infrastructure décide COMMENT.
- Les implémentations enregistrent chaque agrégat vu auprès de l'UoW pour que les events soient publiés au commit.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from domain.aefi_point.aefi_point import AefiPoint
from domain.aefi_point.value_objects.aefi_point_id.aefi_point_id import AefiPointId


class IAefiPointRepository(ABC):
    """
    Responsibility:
        - `add(point)`, `get(point_id)`, `list_by_scan(scan_id)` (comptage des points d'un scan).

    Rationale:
        Sans port de persistance, le comptage des points d'un scan passe par l'état du service applicatif, ce qui signifie que le `Scan` dépend des détails de collecte, ce qui force à modifier la boucle de scan à chaque évolution du handler.

    Design:
        - ABC placée dans `domain/aefi_point/repositories/` (convention `calibration/repositories/`).
        - Chaque implémentation appelle `uow.register(point)` sur les agrégats qu'elle voit.
    """
    @abstractmethod
    def add(self, point: AefiPoint) -> None:
        """Persiste un point (nouveau ou mis à jour)."""

    @abstractmethod
    def get(self, point_id: AefiPointId) -> Optional[AefiPoint]:
        """Retourne le point, ou None s'il est inconnu."""

    @abstractmethod
    def list_by_scan(self, scan_id: UUID) -> List[AefiPoint]:
        """Retourne tous les points référençant ce scan."""
