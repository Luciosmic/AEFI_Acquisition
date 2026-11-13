"""
Scan Repository Port

Responsibility:
- Contrat de persistance de l'agrégat Scan.

Rationale:
- Le handler de clôture charge et sauvegarde le Scan dans sa propre transaction ;
  sans port, il dépendrait d'un stockage concret.

Design:
- Le domaine déclare QUOI persister ; l'infrastructure décide COMMENT.
- Les implémentations enregistrent chaque agrégat vu auprès de l'UoW.
"""

from abc import ABC, abstractmethod
from typing import Optional

from domain.scan.scan import Scan
from domain.scan.value_objects.scan_id.scan_id import ScanId


class IScanRepository(ABC):
    """
    Responsibility:
        - Contrat `add` / `get` de l'agrégat `Scan`.

    Rationale:
        Sans port de persistance, le handler de clôture dépendrait d'un stockage concret, ce qui signifie un domaine non testable sans infrastructure.

    Design:
        - ABC pure ; `get` retourne `None` si inconnu (le handler décide quoi en faire).
    """
    @abstractmethod
    def add(self, scan: Scan) -> None:
        """Persiste un scan (nouveau ou mis à jour)."""

    @abstractmethod
    def get(self, scan_id: ScanId) -> Optional[Scan]:
        """Retourne le scan, ou None s'il est inconnu."""
