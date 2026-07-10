# continuous_acquisition_failed — Intention

## Rationale

Modéliser l'échec de la boucle d'acquisition continue (exception) comme un fait immuable passé, découplé de la UI et de l'infrastructure d'exécution.

## Responsibility

- Signale qu'une acquisition continue a échoué suite à une exception.
- Porte l'identifiant de l'acquisition et la raison de l'échec.

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
- Séparé des `scan_events` pour préserver la cohésion sémantique : scan = mesure positionnée, acquisition continue = stream brut.
