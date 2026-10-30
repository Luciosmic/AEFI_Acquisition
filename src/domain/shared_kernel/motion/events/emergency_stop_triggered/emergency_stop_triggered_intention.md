# emergency_stop_triggered — Intention

## Rationale

Modéliser le déclenchement d'un arrêt d'urgence comme un fait immuable passé — signal critique déclenchant l'annulation immédiate du scan en cours.

## Responsibility

- Aucun champ : le fait seul de l'occurrence suffit (via `occurred_on` hérité de `DomainEvent`).

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`, sans champ propre.
- Consommé par `StepScanExecutor` pour annuler immédiatement le scan en cours.
