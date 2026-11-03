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
    @abstractmethod
    def add(self, line: AefiLine) -> None:
        """Persiste une ligne (nouvelle ou mise à jour)."""

    @abstractmethod
    def get(self, line_id: AefiLineId) -> Optional[AefiLine]:
        """Retourne la ligne, ou None si elle est inconnue."""

    @abstractmethod
    def list_by_scan(self, scan_id: UUID) -> List[AefiLine]:
        """Retourne les lignes référençant ce scan, triées par `line_index`."""
