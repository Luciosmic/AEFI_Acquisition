"""
Inertial Probe Acquisition Executor Port Interface

Responsibility:
- Abstract interface for continuous (streaming) acquisition execution of the
  inertial probe.

Rationale:
- The application layer depends on this port instead of direct threading code.
  Infrastructure implements the worker (same role as
  IElectricFieldProbeAcquisitionExecutor for the field probe).

Design:
- Abstract Base Class (ABC), pure interface.
- start() must not block the caller: stream_port.start_stream() blocks ~0.5 s
  on the real board and has to run in the worker thread, never in the Qt thread.
"""

from abc import ABC, abstractmethod

from application.inertial_probe.inertial_probe_service.dtos.inertial_probe_dtos import (
    InertialProbeAcquisitionConfig,
)
from application.inertial_probe.inertial_probe_service.ports.i_inertial_probe_stream_port import (
    IInertialProbeStreamPort,
)


class IInertialProbeAcquisitionExecutor(ABC):
    """
    Port for starting / stopping continuous inertial probe acquisition.

    Responsibility:
        - Déclarer `start(config, stream_port)` (non bloquant pour l'appelant),
          `stop()` et `is_running()`.

    Rationale:
        `start_stream` bloque ~0,5 s et `read_sample` bloque jusqu'à la prochaine
        ligne : si le service les appelait directement depuis le thread de
        l'interface, le panneau se figerait à chaque démarrage. La mécanique
        d'exécution (thread, boucle, tolérance aux échecs) est de l'infrastructure ;
        le service applicatif reste un délégateur mince, testable sans thread réel.

    Design:
        - **Port outbound** dans `inertial_probe_service/ports/`.
        - Implémenté par `InertialProbeAcquisitionExecutor` dans
          `infrastructure/execution/`.
        - La politique de tolérance aux échecs vit dans l'implémentation, pas dans le
          contrat.
        - Même forme que `IElectricFieldProbeAcquisitionExecutor`, sans correction de
          fréquence (aucun équivalent pour ce capteur).
    """

    @abstractmethod
    def start(
        self,
        config: InertialProbeAcquisitionConfig,
        stream_port: IInertialProbeStreamPort,
    ) -> None:
        """Start continuous acquisition (non-blocking from the caller perspective)."""

    @abstractmethod
    def stop(self) -> None:
        """Request graceful stop; the worker stops the stream on the board."""

    @abstractmethod
    def is_running(self) -> bool:
        """True if the acquisition worker is currently active."""
