# Presenters — Couche Interface

## Rationale
Ce dossier contient les presenters PySide6 qui servent de pont entre les services applicatifs et les widgets UI. Chaque presenter implémente le port de sortie correspondant à son service et émet des signaux Qt vers les panels de l'interface.

## Responsibility
- `ScanPresenter` : implémenter `IScanOutputPort`. Reçoit les événements de scan du service (started, progress, completed, failed, paused, resumed) et les convertit en signaux Qt (`scan_started`, `scan_progress`, etc.). Calcule l'ETA en temps réel via un moyennage glissant. Expose des `@Slot` pour les actions utilisateur (start, pause, resume, cancel, export).
- `MotionPresenter` : recevoir les événements domaine de mouvement (`PositionUpdated`, `MotionCompleted`, `MotionFailed`) via le bus et émettre les signaux UI (`position_updated`, `status_updated`, `operation_failed`). Expose des slots pour les commandes de jog, homing et stop.
- `HardwareAdvancedConfigPresenter` : interroger `HardwareConfigurationService` pour lister les équipements disponibles et charger leurs paramètres. Expose des slots pour la sélection du hardware et l'application de configuration.

## Design
- Chaque presenter hérite de `QObject` et du port de sortie qu'il implémente (`IScanOutputPort` pour `ScanPresenter`).
- Les presenters s'enregistrent comme port de sortie dans leur `__init__` via `service.set_output_port(self)`.
- Aucun import domaine direct : les données circulent uniquement sous forme de DTOs ou de types primitifs dans les signaux Qt.
- Les calculs métier (ETA) sont effectués dans le presenter à titre exceptionnel car l'information de durée par point n'est pas disponible dans le service.
