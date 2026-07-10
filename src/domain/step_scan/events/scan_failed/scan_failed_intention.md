# scan_failed — Intention

## Rationale

Modéliser l'échec d'un scan comme un fait immuable passé, avec la raison explicative pour l'UI et les logs.

## Responsibility

- `scan_id` : identifiant du scan.
- `reason` : raison explicative de l'échec.

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
