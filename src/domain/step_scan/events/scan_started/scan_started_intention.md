---
type: evenement-de-domaine::solidai-ddd
tldr: "scan_id : identifiant du scan démarré."
code: ["[[src/domain/step_scan/events/scan_started/scan_started.py]]"]
cause_de_changement: regle-metier
part_of: "[[src/domain/step_scan/step_scan_intention]]"
---
# scan_started — Intention

## Rationale

Modéliser le démarrage d'un scan comme un fait immuable passé, portant la config complète pour que l'UI puisse calculer le total_points sans requêter l'agrégat.

## Responsibility

- `scan_id` : identifiant du scan démarré.
- `config` : config complète au moment du démarrage — `StepScanConfig` (grille) ou `LineScanConfig` (ligne theta). Les consommateurs discriminent par type.

## Design

- `@dataclass(frozen=True)` héritant de `DomainEvent`.
