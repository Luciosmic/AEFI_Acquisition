"""
NardaPoint Repository Port

Responsibility:
- Contrat de persistance des agrégats NardaPoint.

Rationale:
- Sans port, le comptage des points de champ d'un scan passerait par l'état du service applicatif.

Design:
- Le domaine déclare QUOI persister ; l'infrastructure décide COMMENT.
- Les implémentations enregistrent chaque agrégat vu auprès de l'UoW pour que les events soient publiés au commit.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from domain.narda_point.narda_point import NardaPoint
from domain.narda_point.value_objects.narda_point_id.narda_point_id import NardaPointId


class INardaPointRepository(ABC):
    """
    Responsibility:
        - `add(point)`, `get(point_id)`, `list_by_scan(scan_id)`.

    Rationale:
        Sans port de persistance, le commit d'un point de champ ne publierait jamais `NardaPointAcquired` après transaction, et le `Scan` ne saurait pas que ses mesures de champ sont complètes.

    Design:
        - ABC placée dans `domain/narda_point/repositories/` (même forme que `IAefiPointRepository`).
        - Chaque implémentation appelle `uow.register(point)` sur les agrégats qu'elle voit.
    """
    @abstractmethod
    def add(self, point: NardaPoint) -> None:
        """Persiste un point (nouveau ou mis à jour)."""

    @abstractmethod
    def get(self, point_id: NardaPointId) -> Optional[NardaPoint]:
        """Retourne le point, ou None s'il est inconnu."""

    @abstractmethod
    def list_by_scan(self, scan_id: UUID) -> List[NardaPoint]:
        """Retourne tous les points référençant ce scan."""
