---
type: value-object::solidai-ddd
tldr: "Porter la hauteur de la table, en mm, telle que l'opérateur la donne (il la lit sur le panneau de commande de la table)."
code: ["[[src/domain/frequency_sweep/value_objects/table_height/table_height.py]]"]
cause_de_changement: regle-metier
part_of: "[[src/domain/frequency_sweep/frequency_sweep_intention]]"
---
# table_height — Intention

## Rationale

Un fond n'est réutilisable, ou combinable avec un autre, qu'à hauteur de table égale. Le logiciel ne pilote pas la table et ne la mesure pas : sans hauteur saisie avec chaque balayage, rien ne permet de retrouver à quelle hauteur un fond a été acquis.

## Responsibility

- Porter la hauteur de la table, en mm, telle que l'opérateur la donne (il la lit sur le panneau de commande de la table).

## Design

- `@dataclass(frozen=True)`, un nombre fini de mm. Aucune borne : le logiciel ne connaît pas l'échelle du panneau de la table.
- Grandeur distincte du lift-off de l'objet (sphères ↔ sommet de l'objet).
- Domaine pur.
