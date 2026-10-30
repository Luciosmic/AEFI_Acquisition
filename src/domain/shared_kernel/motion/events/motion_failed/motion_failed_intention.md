# motion_failed — Intention

## Rationale

Modéliser l'échec d'un déplacement comme un fait immuable passé. Utilisé par `StepScanExecutor` pour déclencher l'arrêt du scan en cours.

## Responsibility

- `motion_id` : identifiant du mouvement en échec — corrélation avec le mouvement démarré.
- `error` : message d'erreur associé à l'échec.

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
- **`motion_id`** : corrélation avec `_pending_motion_id` dans `StepScanExecutor` pour éviter les faux positifs de synchronisation.
