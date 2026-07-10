# motion_started — Intention

## Rationale

Modéliser le démarrage d'un déplacement du système de motion comme un fait immuable passé. Utilisé par `StepScanExecutor` et les presenters pour la synchronisation event-based avec le hardware Arcus (asynchrone par nature).

## Responsibility

- `motion_id` : identifiant unique du mouvement démarré.
- `target_position` : `Position2D` visée par le mouvement.

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
- **`motion_id`** : corrélation avec `MotionCompleted`/`MotionFailed` pour éviter les faux positifs de synchronisation.
