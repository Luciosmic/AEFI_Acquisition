# motion_conversion_status_dto — Intention

## Rationale

Sans DTO d'état, le presenter devrait importer les événements domain ou interroger le port pour savoir si le banc peut bouger, et le bandeau « non calibré » ne pourrait pas dire quoi saisir.

## Responsibility

- Dire si la conversion mm/impulsion est appliquée et, sinon, quel moteur, quelle grandeur manque et où la saisir.

## Design

- `@dataclass(frozen=True)`, primitives uniquement.
- Fourni par `MotionControlService.get_conversion_status()`.
