"""
AefiLine Repository Port

Responsibility:
- Contrat de persistance des agrégats AefiLine.

Rationale:
- Le handler de Scan compte les lignes acquises dans une transaction séparée, et l'export relit les
  lignes d'un scan ; sans port, ils liraient l'état du service applicatif.

Design:
- Le domaine déclare QUOI persister ; l'infrastructure décide COMMENT.
- Les implémentations enregistrent chaque agrégat vu auprès de l'UoW pour que les events soient publiés au commit.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from domain.aefi_line.aefi_line import AefiLine
from domain.aefi_line.value_objects.aefi_line_id.aefi_line_id import AefiLineId


class IAefiLineRepository(ABC):
    """
    Responsibility:
        - `add(line)`, `get(line_id)`, `list_by_scan(scan_id)` (trié par `line_index`).

    Rationale:
        Sans port de persistance, le comptage et la relecture des lignes d'un scan passent par l'état du service applicatif, ce qui signifie que le `Scan` et l'export dépendent des détails de la boucle fly, ce qui force à la modifier à chaque évolution du handler.

    Design:
        - ABC placée dans `domain/aefi_line/repositories/`, comme `IAefiPointRepository`.
        - Chaque implémentation appelle `uow.register(line)` sur les agrégats qu'elle voit.
    """
    @abstractmethod
    def add(self, line: AefiLine) -> None:
        """Persiste une ligne (nouvelle ou mise à jour)."""

    @abstractmethod
    def get(self, line_id: AefiLineId) -> Optional[AefiLine]:
        """Retourne la ligne, ou None si elle est inconnue."""

    @abstractmethod
    def list_by_scan(self, scan_id: UUID) -> List[AefiLine]:
        """Retourne les lignes référençant ce scan, triées par `line_index`."""
