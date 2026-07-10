# motion_events — Intention

## Rationale

Modéliser les transitions d'état du système de motion (déplacement, arrêt, urgence) comme des événements domain. Utilisés par `StepScanExecutor` pour la synchronisation event-based avec le hardware Arcus (asynchrone par nature).

## Responsibility

- `MotionCompleted` : motion_id + position finale — signal que le mouvement demandé est terminé.
- `MotionFailed` : motion_id + error — signal d'échec, déclenche l'arrêt du scan.
- `MotionStopped` : reason — arrêt intentionnel ou par commande stop.
- `PositionUpdated` : position courante — pour la mise à jour temps réel dans la UI.
- `EmergencyStopTriggered` : signal d'urgence, déclenche l'annulation immédiate du scan.

## Design

- **`motion_id`** dans `MotionCompleted` et `MotionFailed` : corrélation avec `_pending_motion_id` dans `StepScanExecutor` pour éviter les faux positifs de synchronisation.
- Événements domain (pas infrastructure) : l'adaptateur Arcus les publie sur le bus après traduction des signaux hardware.
