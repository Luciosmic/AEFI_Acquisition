# Événements Domaine

## Rationale
Ce dossier définit tous les événements domaine du système AEFI. Les événements permettent de découpler les mutations d'état des effets de bord (mises à jour UI, export, journalisation) en suivant le pattern Domain Event.

## Responsibility
- `DomainEvent` : classe de base immuable (`frozen=True`) portant le timestamp d'occurrence de tout événement.
- `scan_events.py` : événements du cycle de vie du scan (`ScanStarted`, `ScanPointAcquired`, `ScanCompleted`, `ScanFailed`, `ScanCancelled`, `ScanPaused`, `ScanResumed`).
- `motion_events.py` : événements du mouvement (`MotionStarted`, `MotionCompleted`, `MotionFailed`, `PositionUpdated`, `MotionStopped`, `EmergencyStopTriggered`).
- `system_events.py` : événements du cycle de vie système (`SystemReadyEvent`, `SystemStartupFailedEvent`, `SystemShuttingDownEvent`, `SystemShutdownCompleteEvent`).
- `i_domain_event_bus.py` : interface du bus d'événements (contrat publish/subscribe/unsubscribe).

## Design
- Tous les événements sont des dataclasses `frozen=True` héritant de `DomainEvent` : immuables, sans logique.
- Les événements sont publiés sur le bus via leur nom de classe en minuscules (ex. `"scanstarted"`).
- Chaque fichier regroupe les événements d'un même agrégat ou service applicatif pour une navigation O(1).
