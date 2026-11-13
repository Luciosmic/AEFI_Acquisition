---
type: atome::solidai-atome
tldr: "Nommer la promesse refusée : un scan n'accepte que les sources qu'il a déclarées à sa création."
code: ["[[src/domain/scan/errors/scan_source_not_declared_error.py]]"]
cause_de_changement: regle-metier
---
# scan_source_not_declared_error — Intention

## Rationale

Sans ce refus, une acquisition d'une source non déclarée serait comptée ou ignorée en silence, ce qui signifie qu'une faute de câblage (topic écouté mais source non déclarée) passerait inaperçue, ce qui force à découvrir un scan jamais complet par son absence de fin.

## Responsibility

- Nommer la promesse refusée : un scan n'accepte que les sources qu'il a déclarées à sa création.

## Design

- Hérite de `ValueError`, porte `scan_id`, `source` et `acquisition_id`.
