# motion_completed — Intention

## Rationale

Modéliser la fin réussie d'un déplacement comme un fait immuable passé. Utilisé par `StepScanExecutor` pour la synchronisation event-based avec le hardware Arcus (asynchrone par nature).

## Responsibility

- `motion_id` : identifiant du mouvement terminé — corrélation avec le mouvement démarré.
- `final_position` : `Position2D` finale atteinte.
- `duration_ms` : durée du mouvement en millisecondes.

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
- **`motion_id`** : corrélation avec `_pending_motion_id` dans `StepScanExecutor` pour éviter les faux positifs de synchronisation.
