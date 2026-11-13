---
type: value-object::solidai-ddd
tldr: "Nommer ce qu'un balayage caractérise : INSTRUMENT_REFERENCE (table en position basse, sans objet), BACKGROUND (table à la hauteur de travail, sans objet)."
code: ["[[src/domain/frequency_sweep/value_objects/frequency_sweep_role/frequency_sweep_role.py]]"]
cause_de_changement: regle-metier
part_of: "[[src/domain/frequency_sweep/frequency_sweep_intention]]"
---
# frequency_sweep_role — Intention

## Rationale

Le protocole d'acquisition en fréquence enchaîne des balayages acquis de la même façon mais qui ne caractérisent pas la même chose : l'instrument seul (table en position basse), le fond à la hauteur de travail, puis l'objet. Sans rôle explicite, ce qu'un balayage caractérise ne vit que dans le nom de son dossier, et un fond ne peut pas être retrouvé pour être réutilisé ou combiné.

## Responsibility

- Nommer ce qu'un balayage caractérise : `INSTRUMENT_REFERENCE` (table en position basse, sans objet), `BACKGROUND` (table à la hauteur de travail, sans objet), `OBJECT_MEASUREMENT` (même hauteur de table que le fond, objet posé).
- `measures_an_object` : seul le rôle mesure objet porte un objet mesuré.

## Design

- `Enum` ; la valeur est l'identifiant stable écrit dans l'export.
- Le rôle ne change pas la façon d'acquérir.
