# scan_resumed — Intention

## Rationale

Modéliser la reprise d'un scan après pause comme un fait immuable passé.

## Responsibility

- `scan_id` : identifiant du scan.
- `resume_from_point_index` : index de reprise.

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
