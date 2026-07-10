# scan_completed — Intention

## Rationale

Modéliser la complétion réussie d'un scan comme un fait immuable passé.

## Responsibility

- `scan_id` : identifiant du scan.
- `total_points` : nombre total de points acquis.

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
