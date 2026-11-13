"""
Continuous Acquisition Port Interface

Responsibility:
- Abstract interface for continuous (streaming) acquisition execution.

Rationale:
- Application layer depends on this port instead of direct threading or
  hardware code. Infrastructure implements the actual worker.
"""

from abc import ABC, abstractmethod

from application.shared.aefi_acquisition_service.dtos.aefi_acquisition_dtos import AefiAcquisitionConfig
from application.shared.ports.i_acquisition_port import IAcquisitionPort

# Re-export so existing callers that imported from here continue to work
__all__ = ["IAefiAcquisitionExecutor", "AefiAcquisitionConfig"]


class IAefiAcquisitionExecutor(ABC):
    """
    Port for starting / stopping continuous acquisition.

    Responsibility:
        - Déclarer `start(config: AefiAcquisitionConfig, acquisition_port: IAcquisitionPort)`.
        - Déclarer `stop()`.
        - Déclarer `AefiAcquisitionConfig` comme dataclass co-localisée dans ce fichier.

    Rationale:
        Abstraire la mécanique d'exécution de l'acquisition continue (threads, timers, callbacks) derrière un port pour que `AefiAcquisitionService` reste stateless et testable.

    Design:
        - **Port outbound** dans `aefi_acquisition_service/`.
        - `AefiAcquisitionConfig` est défini dans ce même fichier pour éviter une prolifération de modules DTOs pour un type simple.
        - Implémenté par `AefiAcquisitionExecutor` dans `infrastructure/execution/`.
    """

    @abstractmethod
    def start(self, config: AefiAcquisitionConfig, acquisition_port: IAcquisitionPort) -> None:
        """
        Start continuous acquisition (non‑blocking from the caller perspective).
        """

    @abstractmethod
    def stop(self) -> None:
        """Request graceful stop of the continuous acquisition."""

    @abstractmethod
    def is_running(self) -> bool:
        """True if the acquisition worker is currently active."""


