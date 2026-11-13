"""
Electric Field Probe Acquisition Executor Port Interface

Responsibility:
- Abstract interface for continuous (streaming) acquisition execution of an
  electric field probe.

Rationale:
- Application layer depends on this port instead of direct threading code.
  Infrastructure implements the actual worker (mirrors
  IAefiAcquisitionExecutor / AefiAcquisitionExecutor for the AEFI channel).

Design:
- Abstract Base Class (ABC), pure interface.
- start()/stop()/is_running() — same shape as IAefiAcquisitionExecutor so
  both continuous-acquisition channels read the same way.
"""

from abc import ABC, abstractmethod

from application.services.electric_field_probe_service.dtos.electric_field_probe_dtos import (
    ElectricFieldProbeAcquisitionConfig,
)
from application.services.electric_field_probe_service.ports.i_electric_field_probe_port import (
    IElectricFieldProbePort,
)


class IElectricFieldProbeAcquisitionExecutor(ABC):
    """
    Port for starting / stopping continuous electric field probe acquisition.

    Responsibility:
        - Déclarer `start(config: ElectricFieldProbeAcquisitionConfig, probe_port: IElectricFieldProbePort)`.
        - Déclarer `stop()`.
        - Déclarer `is_running() -> bool`.

    Rationale:
        Abstraire la mécanique d'exécution de l'acquisition continue (thread, boucle,
        retry) derrière un port pour que `ElectricFieldProbeService` reste un simple
        délégateur, testable sans thread réel — même rôle que
        `IAefiAcquisitionExecutor` pour le canal AEFI.

    Design:
        - **Port outbound** dans `electric_field_probe_service/ports/`.
        - Implémenté par `ElectricFieldProbeAcquisitionExecutor` dans `infrastructure/execution/`.
        - La politique de retry (`MAX_CONSECUTIVE_SAMPLE_FAILURES`) est une règle
          applicative propre à la sonde Narda (connue pour être flaky) — elle vit
          dans l'implémentation infra de ce port, pas dans le contrat lui-même, et
          n'existe pas côté `AefiAcquisitionExecutor`.
        - Pas de `update_config()` : l'acquisition est best-effort des deux côtés
          (AEFI et sonde), donc il n'y a plus de paramètre de rate à mettre à jour
          à chaud. Historique : `IAefiAcquisitionExecutor` avait un `update_config`
          qui n'était jamais relu par son worker (mort depuis l'origine) — les deux
          ports ont depuis convergé en retirant le concept entièrement plutôt que de
          le réparer.
    """

    @abstractmethod
    def start(
        self,
        config: ElectricFieldProbeAcquisitionConfig,
        probe_port: IElectricFieldProbePort,
    ) -> None:
        """Start continuous acquisition (non-blocking from the caller perspective)."""

    @abstractmethod
    def stop(self) -> None:
        """Request graceful stop of the continuous acquisition."""

    @abstractmethod
    def is_running(self) -> bool:
        """True if the acquisition worker is currently active."""

    @abstractmethod
    def request_frequency_correction(self, frequency_hz: float) -> None:
        """
        Request that the running worker apply a frequency correction on the
        probe at its next loop iteration (non-blocking, no direct port call —
        only the worker thread touches the probe port while streaming).
        """
