# Arcus Performax 4EX — Adaptateur Moteur

## Rationale
Ce module implémente le contrôle des moteurs pas-à-pas Arcus Performax 4EX qui pilotent les axes X et Y du banc de scan. Il isole la dépendance à la bibliothèque `pylablib` et au protocole série propriétaire Arcus derrière les interfaces DDD.

## Responsibility
- `ArcusPerformax4EXController` (`driver_arcus_performax4EX.py`) : encapsuler la communication bas-niveau avec le contrôleur Arcus (connexion, déplacement en steps, homing, lecture position, vitesse). Organisé en QCS (Setup/Command/Query).
- `ArcusAdapter` (`adapter_motion_port_arcus_performax4EX.py`) : implémenter `IMotionPort`. Convertit les positions mm en steps (calibration : µm/step configurable), gère un worker thread et un monitor thread pour asynchroniser les commandes et publier les événements `MotionStarted/Completed/Failed` et `PositionUpdated` sur le bus domaine.
- `ArcusPerformaxLifecycleAdapter` (`adapter_lifecycle_arcus_performax4EX.py`) : implémenter `IHardwareInitializationPort`. Orchestre la connexion du contrôleur et l'activation de l'adaptateur lors du démarrage système.

## Design
- L'architecture worker/monitor sépare la file de commandes (séquentielle) du monitoring de position (polling 150 ms) pour ne jamais bloquer le thread principal.
- La calibration (µm/step) est chargée depuis un fichier JSON local (`arcus_default_config.json`) et peut être mise à jour dynamiquement via `update_calibration()`.
- Le facteur de conversion par défaut est 43,6 µm/step (~22,9 steps/mm).
