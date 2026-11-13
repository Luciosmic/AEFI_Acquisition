---
type: evenement-de-domaine::solidai-ddd
tldr: "scan_id : identifiant du scan."
code: ["[[src/domain/step_scan/events/scan_resumed/scan_resumed.py]]"]
cause_de_changement: regle-metier
part_of: "[[src/domain/step_scan/step_scan_intention]]"
---
# scan_resumed — Intention

## Rationale

Modéliser la reprise d'un scan après pause comme un fait immuable passé.

## Responsibility

- `scan_id` : identifiant du scan.
- `resume_from_point_index` : index de reprise.

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
