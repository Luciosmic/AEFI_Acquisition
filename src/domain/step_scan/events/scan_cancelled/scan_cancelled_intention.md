---
type: evenement-de-domaine::solidai-ddd
tldr: "scan_id : identifiant du scan annulé."
code: ["[[src/domain/step_scan/events/scan_cancelled/scan_cancelled.py]]"]
cause_de_changement: regle-metier
part_of: "[[src/domain/step_scan/step_scan_intention]]"
---
# scan_cancelled — Intention

## Rationale

Modéliser l'annulation d'un scan comme un fait immuable passé.

## Responsibility

- `scan_id` : identifiant du scan annulé.

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
