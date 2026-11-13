---
type: evenement-de-domaine::solidai-ddd
tldr: "scan_id : identifiant du scan."
code: ["[[src/domain/step_scan/events/scan_completed/scan_completed.py]]"]
cause_de_changement: regle-metier
part_of: "[[src/domain/step_scan/step_scan_intention]]"
---
# scan_completed — Intention

## Rationale

Modéliser la complétion réussie d'un scan comme un fait immuable passé.

## Responsibility

- `scan_id` : identifiant du scan.
- `total_points` : nombre total de points acquis.

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
