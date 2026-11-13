---
type: value-object::solidai-ddd
tldr: "Typer l'identité d'une AefiLine."
code: ["[[src/domain/aefi_line/value_objects/aefi_line_id/aefi_line_id.py]]"]
cause_de_changement: regle-metier
part_of: "[[src/domain/aefi_line/aefi_line_intention]]"
---
# aefi_line_id — Intention

## Rationale

Avec des `UUID` bruts, l'identité d'une ligne, celle d'un point et celle d'un scan sont interchangeables pour le vérificateur de types, ce qui laisse passer `repo.get(scan_id)` sans erreur.

## Responsibility

- Typer l'identité d'une `AefiLine`.

## Design

- `NewType` sur `UUID`, comme `AefiPointId` ; le cast se fait aux frontières du domaine : `AefiLineId(uuid4())`.
