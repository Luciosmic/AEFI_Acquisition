---
type: value-object::solidai-ddd
tldr: "Nommer l'identité d'un Scan."
code: ["[[src/domain/scan/value_objects/scan_id/scan_id.py]]"]
cause_de_changement: regle-metier
part_of: "[[src/domain/scan/scan_intention]]"
---
# scan_id — Intention

## Rationale

Sans identité typée, un `scan_id` se confond avec n'importe quel autre UUID (id de point, id d'événement), ce qui signifie qu'une inversion d'arguments passe sans bruit, ce qui force à la découvrir à l'exécution.

## Responsibility

- Nommer l'identité d'un `Scan`.

## Design

- `NewType` sur `UUID`, même forme que `AefiPointId` ; compatible avec les `scan_id` UUID existants.
