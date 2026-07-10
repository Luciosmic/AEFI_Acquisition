# scan_started — Intention

## Rationale

Modéliser le démarrage d'un scan comme un fait immuable passé, portant la config complète pour que l'UI puisse calculer le total_points sans requêter l'agrégat.

## Responsibility

- `scan_id` : identifiant du scan démarré.
- `config` : `StepScanConfig` complète au moment du démarrage.

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
