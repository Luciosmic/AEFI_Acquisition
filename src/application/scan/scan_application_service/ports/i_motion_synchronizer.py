"""
Motion Synchronizer Port

Responsibility:
- Provide the scan loop with a blocking-until-motion-completes primitive
  that returns a typed OperationResult instead of raising.

Rationale:
- The motion port is fire-and-forget: `move_to(position) -> motion_id`.
  Motion completion is signaled asynchronously through domain events on
  the shared bus (MotionCompleted, MotionFailed, MotionStopped,
  EmergencyStopTriggered).
- The scan use-case loop lives in the Application layer and must not
  know that motion completion arrives through an event bus, nor that
  the underlying primitive is a threading.Event. Both are Infrastructure
  concerns.
- This port isolates the "wait for a specific motion_id to complete"
  operation behind an application-owned contract.

Design:
- Single method: wait_for_motion(motion_id, timeout) -> OperationResult.
- Returns typed MotionSyncError on failure (Timeout / HardwareFailed /
  EmergencyStop / StoppedExternally) — never raises for expected outcomes.
- Timeout is configurable per call because different motion segments have
  different physical durations.
- The implementation is expected to subscribe to motion events at
  construction and clean up subscribers on shutdown; the port itself
  does not expose subscribe/unsubscribe (Infrastructure concern).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from application.scan.scan_application_service.errors.motion_sync_error import (
    MotionSyncError,
)
from domain.shared_kernel.operation_result import OperationResult


class IMotionSynchronizer(ABC):
    """
    Port for synchronizing the scan loop with asynchronous motion completion.

    Responsibility:
        - `wait_for_motion(motion_id, timeout_seconds) -> OperationResult[None, MotionSyncError]`
          - Bloque jusqu'à ce que le mouvement identifié atteigne un état terminal
          - Retourne `.ok(None)` si complété normalement
          - Retourne `.fail(MotionSyncError.*)` pour chaque autre issue terminale (Timeout, HardwareFailed, EmergencyStop, StoppedExternally)
          - Ne raise jamais pour les issues attendues

    Rationale:
        `IMotionPort.move_to(position)` est fire-and-forget : la fin réelle du mouvement arrive de façon asynchrone sur le bus d'events (`MotionCompleted`, `MotionFailed`, `MotionStopped`, `EmergencyStopTriggered`). La boucle de scan (Application) a besoin d'un point de rendez-vous propre : « attends la fin de ce `motion_id` ». Sans ce port, l'application devrait s'abonner directement au bus d'events et gérer une `threading.Event` — deux concerns d'infra qui ne lui appartiennent pas.

        Ce port est scoped au `scan_application_service` : c'est le seul consommateur du besoin de synchronisation motion point-à-point.

    Design:
        - Contrat de niveau application. L'implémentation infra (`EventBusMotionSynchronizer`) souscrit aux 4 events motion à la construction, maintient un dict `motion_id → OperationResult` et signale via `threading.Event` par `motion_id`.
        - Le timeout est un paramètre par appel : chaque segment de trajectoire a une durée physique différente (déplacements longs en X vs courts en Y).
        - Le port n'expose pas `subscribe`/`unsubscribe` — c'est du management d'abonnement bus, purement infra.
        - Reproduit dans son Fake toutes les variantes `MotionSyncError` pour satisfaire gate D du pre-pr-quality-check.
    """

    @abstractmethod
    def wait_for_motion(
        self, motion_id: str, timeout_seconds: float
    ) -> OperationResult[None, MotionSyncError]:
        """
        Block until the motion identified by motion_id reaches a terminal state
        (completed, failed, stopped, or aborted by emergency stop) or the
        timeout expires.

        Returns:
            OperationResult.ok(None) when the motion completed normally.
            OperationResult.fail(MotionSyncError.*) for every other terminal
            outcome. Never raises for expected outcomes.
        """
