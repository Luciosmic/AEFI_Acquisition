---
type: evenement-de-domaine::solidai-ddd
tldr: "scan_id : identifiant du scan."
code: ["[[src/domain/step_scan/events/scan_paused/scan_paused.py]]"]
cause_de_changement: regle-metier
part_of: "[[src/domain/step_scan/step_scan_intention]]"
---
# scan_paused — Intention

## Rationale

Modéliser la mise en pause d'un scan comme un fait immuable passé, avec l'index atteint pour permettre une reprise cohérente.

## Responsibility

- `scan_id` : identifiant du scan.
- `current_point_index` : index atteint au moment de la pause.

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
