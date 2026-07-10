# continuous_acquisition_stopped — Intention

## Rationale

Modéliser l'arrêt (normal ou après échec) de l'acquisition continue comme un fait immuable passé, pour permettre à la UI et aux services de réagir sans dépendance directe sur l'exécuteur.

## Responsibility

- Signale qu'une acquisition continue s'est arrêtée, normalement ou après un échec.
- Porte l'identifiant de l'acquisition concernée.

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
- Séparé des `scan_events` pour préserver la cohésion sémantique : scan = mesure positionnée, acquisition continue = stream brut.
