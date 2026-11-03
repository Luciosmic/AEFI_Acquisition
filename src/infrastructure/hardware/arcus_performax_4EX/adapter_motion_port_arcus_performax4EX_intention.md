# adapter_motion_port_arcus_performax4EX — Intention

## Rationale

Adaptateur Real implémentant `IMotionPort` pour le contrôleur Arcus Performax 4EX via la DLL propriétaire. C'est l'unique point d'entrée de la DLL Arcus dans l'architecture DDD — toute la logique de motion reste dans les services domain/application.

## Responsibility

- Implémenter `move_to(position) → str` : commander le déplacement et retourner un `motion_id` unique pour la synchronisation event-based.
- Implémenter `stop()`, `emergency_stop()`, `home(axis)`, `get_current_position()`, `set_reference()`, `get_axis_limits()`.
- Publier `MotionCompleted`, `MotionFailed`, `PositionUpdated` sur `IDomainEventBus` après chaque opération asynchrone.

## Design

- **Dépend de `DriverArcusPerformax4EX`** pour les appels DLL bas-niveau.
- **Publie des événements domain** (pas des callbacks directs) : `StepScanExecutor` souscrit au bus pour la synchronisation.
- `motion_id` est un UUID généré à chaque `move_to()` — corrélation avec `MotionCompleted.motion_id`.
- **Sans conversion mm/impulsion** (`set_microns_per_pulse` jamais appelé) : `move_to`, `set_speed`, `get_current_position`, `get_cruise_speed_mm_s` lèvent `MotionConversionUnavailableError` ; `is_conversion_available()` expose l'état ; `stop`/`emergency_stop`/`set_speed_mode` (impulsions) restent disponibles. La boucle de surveillance se met en pause avec un seul avertissement, sans trace d'erreur par cycle. Aucune valeur par défaut silencieuse.
