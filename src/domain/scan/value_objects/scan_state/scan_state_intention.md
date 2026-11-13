---
type: value-object::solidai-ddd
tldr: "Énumérer le cycle de vie minimal du Scan : PENDING, STARTED, COMPLETED."
code: ["[[src/domain/scan/value_objects/scan_state/scan_state.py]]"]
cause_de_changement: regle-metier
part_of: "[[src/domain/scan/scan_intention]]"
---
# scan_state — Intention

## Rationale

Sans état PENDING explicite, un scan créé et un scan démarré sont indiscernables, ce qui signifie qu'on ne peut pas observer « prêt mais pas lancé », ce qui force à déduire l'état depuis l'existence de points.

## Responsibility

- Énumérer le cycle de vie minimal du `Scan` : PENDING, STARTED, COMPLETED.

## Design

- Distinct de `step_scan.ScanStatus` (non migré : pause, cancel, failed restent là-bas).
