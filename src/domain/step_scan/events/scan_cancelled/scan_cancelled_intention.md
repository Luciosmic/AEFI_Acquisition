# scan_cancelled — Intention

## Rationale

Modéliser l'annulation d'un scan comme un fait immuable passé.

## Responsibility

- `scan_id` : identifiant du scan annulé.

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
