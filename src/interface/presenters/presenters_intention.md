# Presenters — Couche Interface

## Rationale
Ce dossier contient les presenters PySide6 qui servent de pont entre les services applicatifs et les widgets UI. Chaque presenter implémente le port de sortie correspondant à son service et émet des signaux Qt vers les panels de l'interface.

## Responsibility
- `ScanPresenter` : implémenter `IScanOutputPort`. Reçoit les événements de scan du service (started, progress, completed, failed, paused, resumed) et les convertit en signaux Qt (`scan_started`, `scan_progress`, etc.). Calcule l'ETA en temps réel via un moyennage glissant. Expose des `@Slot` pour les actions utilisateur (start, pause, resume, cancel, export).
- `MotionPresenter` : recevoir les événements domaine de mouvement (`PositionUpdated`, `MotionCompleted`, `MotionFailed`) via le bus et émettre les signaux UI (`position_updated`, `status_updated`, `operation_failed`). Expose des slots pour les commandes de jog, homing et stop.
- `HardwareAdvancedConfigPresenter` : interroger `HardwareConfigurationService` pour lister les équipements disponibles et charger leurs paramètres. Expose des slots pour la sélection du hardware et l'application de configuration. S'abonne aussi à `ExcitationFrequencyChanged`/`DdsChannelConfigChanged`/`ExcitationDdsLinkChanged` pour patcher en place (`_patch_specs_by_key`) les specs déjà chargées quand le panel Excitation change directement la fréquence, le gain/phase des canaux 1/2, ou le lien DDS1-DDS2 — jamais un re-fetch complet, qui écraserait une édition non sauvegardée du panel. `reset_configuration_to_default()` fait l'inverse volontairement : un reset touche potentiellement tous les champs à la fois, donc il re-fetch la liste complète des specs (comme `select_hardware()`) plutôt que de patcher.
- `ExcitationPresenter` : pont entre `ExcitationConfigurationService` et `ExcitationPanel`. `refresh_state()` pousse mode/niveaux/fréquence/lien vers l'UI (`excitation_updated`, `link_state_changed`) au démarrage et à chaque changement externe (Hardware Advanced Config, via abonnement à `ExcitationFrequencyChanged`/`DdsChannelConfigChanged`/`ExcitationDdsLinkChanged`). `on_excitation_changed`/`on_link_toggled` sont les slots pour les actions utilisateur du panel.

## Design
- Chaque presenter hérite de `QObject` et du port de sortie qu'il implémente (`IScanOutputPort` pour `ScanPresenter`).
- Les presenters s'enregistrent comme port de sortie dans leur `__init__` via `service.set_output_port(self)`.
- Aucun import domaine direct : les données circulent uniquement sous forme de DTOs ou de types primitifs dans les signaux Qt.
- Les calculs métier (ETA) sont effectués dans le presenter à titre exceptionnel car l'information de durée par point n'est pas disponible dans le service.
