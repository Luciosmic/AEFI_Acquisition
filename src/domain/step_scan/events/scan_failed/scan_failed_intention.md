---
type: evenement-de-domaine::solidai-ddd
tldr: "scan_id : identifiant du scan."
code: ["[[src/domain/step_scan/events/scan_failed/scan_failed.py]]"]
cause_de_changement: regle-metier
part_of: "[[src/domain/step_scan/step_scan_intention]]"
---
# scan_failed — Intention

## Rationale

Modéliser l'échec d'un scan comme un fait immuable passé, avec la raison explicative pour l'UI et les logs.

## Responsibility

- `scan_id` : identifiant du scan.
- `reason` : raison explicative de l'échec.

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
