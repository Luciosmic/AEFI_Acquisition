"""
Acquisition Snapshot Port Interface

Responsibility:
- Return the acquisition context as a flat dict of sections, for inclusion
  in the per-scan metadata JSON: the hardware configuration known to the
  domain (mounted boards and their characterization, sensor and source
  geometry calibrations, with the warnings of an incomplete configuration)
  and the last-applied hardware configs sitting on disk.

Rationale:
- AD9106/motion config have no in-memory getter today — the on-disk JSON
  files they're persisted to are the only accessible source of truth.
  Reading them from the application layer directly would violate the
  "no direct IO in Application services" rule, hence this port.

Design:
- Single read-only query method; no state, no configuration step.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class IAcquisitionSnapshotPort(ABC):
    """
    Read-only snapshot of on-disk acquisition/hardware config sections.

    Responsibility:
        - Une requête en lecture seule, `read()`, qui rend ces faits sous forme de
          dict (`hardware_configuration`, `hardware_settings`, …).
        - Ne jamais lever : une source absente ou illisible devient un avertissement,
          pas une exception.

    Rationale:
        Une partie des conditions matérielles vit dans des registres domaine
        (catalogue des composants, calibrations), une autre dans des fichiers de
        config sur disque (AD9106, ADS131A04, MCU résolus `default + last`). Il fallait
        un seul endroit qui les rassemble, sans que le code qui les consomme connaisse
        les noms et formats de fichiers.

    Design:
        - ABC pure. Implémenté par `infrastructure/persistence/acquisition_snapshot_reader.py`.
        - Depuis le 2026-10-02, son seul consommateur est
          `infrastructure/acquisition_conditions_reader/acquisition_conditions_reader.py`,
          qui le traduit en `AcquisitionConditionsDTO` pour tous les exports
          (`IAcquisitionConditionsPort`). `ScanExportService` ne le lit plus.
          `ponytail:` le port reste dans le dossier du service d'export alors qu'il ne
          sert plus qu'entre deux adaptateurs ; à déplacer en infrastructure le jour où
          il change.
    """

    @abstractmethod
    def read(self) -> Dict[str, Any]:
        """Return available config sections, keyed by section name.

        Missing or unreadable files are simply omitted from the result —
        never raises.
        """
        pass
