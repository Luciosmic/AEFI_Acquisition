---
type: value-object::solidai-ddd
tldr: "Définir PENDING, RUNNING, PAUSED, COMPLETED, FAILED, CANCELLED."
code: ["[[src/domain/step_scan/value_objects/scan_status/scan_status.py]]"]
cause_de_changement: regle-metier
part_of: "[[src/domain/step_scan/step_scan_intention]]"
---
# scan_status — Intention

## Rationale

Enum domain représentant les états possibles d'un scan. Typer les états évite les comparaisons de strings dans la logique de transition et permet l'exhaustivité des branches (mypy/pyright).

## Responsibility

- Définir PENDING, RUNNING, PAUSED, COMPLETED, FAILED, CANCELLED.
- Fournir `is_final() → bool` pour déterminer si de nouvelles transitions sont possibles.

## Design

- **`enum.Enum`** (ou `enum.auto()`).
- `is_final()` : COMPLETED, FAILED, CANCELLED sont des états finaux — aucune transition possible après.
- Utilisé dans `SpatialScan`, `StepScan`, `ScanApplicationService`, `StepScanExecutor`.
