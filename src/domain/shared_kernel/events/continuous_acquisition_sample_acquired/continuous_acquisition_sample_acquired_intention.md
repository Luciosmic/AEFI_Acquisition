# continuous_acquisition_sample_acquired — Intention

## Rationale

Modéliser la réception d'un échantillon d'acquisition continue (streaming temps réel) comme un événement domain distinct des événements de scan step-by-step. Permet à la UI d'afficher un oscilloscope en direct sans dépendance directe sur l'exécuteur.

## Responsibility

- Signale qu'un nouvel échantillon de tension a été acquis dans le cadre d'une acquisition continue.
- Porte l'identifiant de l'acquisition, l'index de l'échantillon et la mesure (`AefiVoltageMeasurement`).

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
- Séparé des `scan_events` pour préserver la cohésion sémantique : scan = mesure positionnée, acquisition continue = stream brut.
