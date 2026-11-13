# i_motion_synchronizer — Intention

## Rationale

`IMotionPort.move_to(position)` est fire-and-forget : la fin réelle du mouvement arrive de façon asynchrone sur le bus d'events (`MotionCompleted`, `MotionFailed`, `MotionStopped`, `EmergencyStopTriggered`). La boucle de scan (Application) a besoin d'un point de rendez-vous propre : « attends la fin de ce `motion_id` ». Sans ce port, l'application devrait s'abonner directement au bus d'events et gérer une `threading.Event` — deux concerns d'infra qui ne lui appartiennent pas.

Ce port est scoped au `scan_application_service` : c'est le seul consommateur du besoin de synchronisation motion point-à-point.

## Responsibility

- `wait_for_motion(motion_id, timeout_seconds) -> OperationResult[None, MotionSyncError]`
  - Bloque jusqu'à ce que le mouvement identifié atteigne un état terminal
  - Retourne `.ok(None)` si complété normalement
  - Retourne `.fail(MotionSyncError.*)` pour chaque autre issue terminale (Timeout, HardwareFailed, EmergencyStop, StoppedExternally)
  - Ne raise jamais pour les issues attendues

## Design

- Contrat de niveau application. L'implémentation infra (`EventBusMotionSynchronizer`) souscrit aux 4 events motion à la construction, maintient un dict `motion_id → OperationResult` et signale via `threading.Event` par `motion_id`.
- Le timeout est un paramètre par appel : chaque segment de trajectoire a une durée physique différente (déplacements longs en X vs courts en Y).
- Le port n'expose pas `subscribe`/`unsubscribe` — c'est du management d'abonnement bus, purement infra.
- Reproduit dans son Fake toutes les variantes `MotionSyncError` pour satisfaire gate D du pre-pr-quality-check.
