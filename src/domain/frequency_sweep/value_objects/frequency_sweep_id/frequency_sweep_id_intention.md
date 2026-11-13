---
type: value-object::solidai-ddd
tldr: "Typer l'identité d'un FrequencySweep."
code: ["[[src/domain/frequency_sweep/value_objects/frequency_sweep_id/frequency_sweep_id.py]]"]
cause_de_changement: regle-metier
part_of: "[[src/domain/frequency_sweep/frequency_sweep_intention]]"
---
# frequency_sweep_id — Intention

## Rationale

Une mesure objet référencera son fond par identité. Avec des `UUID` bruts, l'identité d'un balayage et celle d'un scan ou d'un point sont interchangeables pour le vérificateur de types.

## Responsibility

- Typer l'identité d'un `FrequencySweep`.

## Design

- `NewType` sur `UUID` (convention `AefiPointId`) ; le cast se fait aux frontières du domaine : `FrequencySweepId(uuid4())`.
